import asyncio
import logging
import re
import uuid
from collections.abc import Collection, Iterable, Sequence
from dataclasses import dataclass
from http import HTTPStatus
from typing import Final, override

from aiohttp import web
from aiohttp.typedefs import Handler, Middleware
from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.propagate import extract
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import (
    ALWAYS_ON,
    Decision,
    ParentBased,
    Sampler,
    SamplingResult,
)
from opentelemetry.trace import Link, SpanKind, StatusCode, TraceState
from opentelemetry.util.types import Attributes

from ai.backend.logging.formatter import CustomJsonFormatter

_UNTRACED_PATH: Final = re.compile(r"^/(health|metrics|livez|readyz)(/|$)")
_UNMATCHED_ROUTE: Final = "<unmatched>"


@dataclass
class OpenTelemetrySpec:
    service_name: str
    service_version: str
    log_level: str
    endpoint: str
    service_instance_id: uuid.UUID
    service_instance_name: str
    max_queue_size: int
    max_export_batch_size: int

    def to_resource(self) -> Resource:
        attributes = {
            "service.name": self.service_name,
            "service.version": self.service_version,
            "service.instance.id": str(self.service_instance_id),
            "service.instance.name": self.service_instance_name,
        }
        return Resource.create(attributes)


def apply_otel_loggers(loggers: Iterable[logging.Logger], spec: OpenTelemetrySpec) -> None:
    log_provider = LoggerProvider(
        resource=spec.to_resource(),
    )
    otlp_log_exporter = OTLPLogExporter(endpoint=spec.endpoint)
    log_processor = BatchLogRecordProcessor(otlp_log_exporter)
    log_provider.add_log_record_processor(log_processor)
    log_level = logging.getLevelNamesMapping().get(spec.log_level.upper(), logging.INFO)
    handler = LoggingHandler(level=log_level, logger_provider=log_provider)

    # Apply JSON formatter to handler for OTEL
    json_formatter = CustomJsonFormatter()
    handler.setFormatter(json_formatter)

    logging.getLogger().addHandler(handler)
    for logger in loggers:
        logger.addHandler(handler)
        # Apply JSON formatter to existing handlers for extra fields
        for existing_handler in logger.handlers:
            existing_handler.setFormatter(json_formatter)
    logging.info("open telemetry logging initialized successfully.")


class RootClientDropSampler(Sampler):
    """Follows the parent's decision, and drops a CLIENT span that has no parent.

    Background polls (health probes and the like) would otherwise each start a trace.
    """

    _parent_based: ParentBased

    def __init__(self) -> None:
        self._parent_based = ParentBased(ALWAYS_ON)

    @override
    def should_sample(
        self,
        parent_context: Context | None,
        trace_id: int,
        name: str,
        kind: SpanKind | None = None,
        attributes: Attributes = None,
        links: Sequence[Link] | None = None,
        trace_state: TraceState | None = None,
    ) -> SamplingResult:
        parent = trace.get_current_span(parent_context).get_span_context()
        if kind is SpanKind.CLIENT and not parent.is_valid:
            return SamplingResult(Decision.DROP)
        return self._parent_based.should_sample(
            parent_context, trace_id, name, kind, attributes, links, trace_state
        )

    @override
    def get_description(self) -> str:
        return "RootClientDropSampler"


def apply_otel_tracer(spec: OpenTelemetrySpec) -> None:
    tracer_provider = TracerProvider(resource=spec.to_resource(), sampler=RootClientDropSampler())
    span_exporter = OTLPSpanExporter(endpoint=spec.endpoint)
    span_processor = BatchSpanProcessor(
        span_exporter,
        max_queue_size=spec.max_queue_size,
        max_export_batch_size=spec.max_export_batch_size,
    )
    tracer_provider.add_span_processor(span_processor)
    trace.set_tracer_provider(tracer_provider)
    logging.info("OpenTelemetry tracing initialized successfully.")


def instrument_aiohttp_client() -> None:
    AioHttpClientInstrumentor().instrument()
    logging.info("OpenTelemetry tracing for aiohttp client initialized successfully.")


def _record_response_status(span: trace.Span, status: int) -> None:
    span.set_attribute("http.response.status_code", status)
    if status >= HTTPStatus.INTERNAL_SERVER_ERROR:
        span.set_status(StatusCode.ERROR)


def build_otel_server_middleware(
    untraced_handlers: Collection[Handler] = (),
    parent_required_prefixes: Collection[str] = (),
) -> Middleware:
    """Open a SERVER span per request, except for health, metrics and ``untraced_handlers``.

    Under ``parent_required_prefixes``, only a request carrying the caller's trace context is traced.
    """
    prefixes = tuple(parent_required_prefixes)

    @web.middleware
    async def otel_server_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
        if _UNTRACED_PATH.match(request.path) or request.match_info.handler in untraced_handlers:
            return await handler(request)
        parent_context = extract(request.headers)
        if (
            request.path.startswith(prefixes)
            and not trace.get_current_span(parent_context).get_span_context().is_valid
        ):
            return await handler(request)
        resource = request.match_info.route.resource
        route = resource.canonical if resource is not None else _UNMATCHED_ROUTE
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(
            f"{request.method} {route}",
            context=parent_context,
            kind=SpanKind.SERVER,
            attributes={
                "http.request.method": request.method,
                "http.route": route,
                "url.path": request.path,
            },
            record_exception=False,
            set_status_on_exception=False,
        ) as span:
            try:
                response = await handler(request)
            except web.HTTPException as e:
                _record_response_status(span, e.status)
                raise
            except asyncio.CancelledError:
                # The client went away; there is no response status to record.
                raise
            except Exception as e:
                span.record_exception(e)
                _record_response_status(span, HTTPStatus.INTERNAL_SERVER_ERROR)
                raise
            _record_response_status(span, response.status)
            return response

    return otel_server_middleware
