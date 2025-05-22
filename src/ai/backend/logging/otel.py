import logging
from dataclasses import dataclass

from aiohttp import web
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.aiohttp_server import AioHttpServerInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class OpenTelemetrySpec:
    service_id: str
    service_name: str
    service_version: str
    endpoint: str


def initialize_opentelemetry(spec: OpenTelemetrySpec) -> None:
    resource = Resource.create({
        "service.name": spec.service_name,
        "service.id": spec.service_id,
        "service.version": spec.service_version,
    })
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    otlp_trace_exporter = OTLPSpanExporter(endpoint=spec.endpoint)
    span_processor = BatchSpanProcessor(otlp_trace_exporter)
    tracer_provider.add_span_processor(span_processor)

    log_provider = LoggerProvider(resource=resource)
    otlp_log_exporter = OTLPLogExporter(endpoint=spec.endpoint)
    log_processor = BatchLogRecordProcessor(otlp_log_exporter)
    log_provider.add_log_record_processor(log_processor)

    handler = LoggingHandler(level=logging.INFO, logger_provider=log_provider)
    logging.getLogger().addHandler(handler)
    LoggingInstrumentor().instrument(set_logging_format=False, logger_provider=log_provider)


def instrument_aiohttp_server(app: web.Application):
    AioHttpServerInstrumentor().instrument(app)
    log.info("OpenTelemetry tracing for aiohttp server initialized successfully.")
