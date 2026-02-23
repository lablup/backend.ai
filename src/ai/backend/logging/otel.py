import logging
import uuid
from collections.abc import Iterable
from dataclasses import dataclass

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.instrumentation.aiohttp_server import AioHttpServerInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from ai.backend.logging.formatter import CustomJsonFormatter


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


def apply_otel_tracer(spec: OpenTelemetrySpec) -> None:
    tracer_provider = TracerProvider(resource=spec.to_resource())
    span_exporter = OTLPSpanExporter(endpoint=spec.endpoint)
    span_processor = BatchSpanProcessor(
        span_exporter,
        max_queue_size=spec.max_queue_size,
        max_export_batch_size=spec.max_export_batch_size,
    )
    tracer_provider.add_span_processor(span_processor)
    trace.set_tracer_provider(tracer_provider)
    logging.info("OpenTelemetry tracing initialized successfully.")


def instrument_aiohttp_server() -> None:
    AioHttpServerInstrumentor().instrument()
    logging.info("OpenTelemetry tracing for aiohttp server initialized successfully.")


def instrument_aiohttp_client() -> None:
    AioHttpClientInstrumentor().instrument()
    logging.info("OpenTelemetry tracing for aiohttp client initialized successfully.")
