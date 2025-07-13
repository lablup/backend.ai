import logging
import uuid
from dataclasses import dataclass
from typing import Iterable

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
    service_id: uuid.UUID
    service_name: str
    service_version: str
    log_level: str
    endpoint: str

    def to_resource(self) -> Resource:
        return Resource.create({
            "service.name": self.service_name,
            "service.id": str(self.service_id),
            "service.version": self.service_version,
        })


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
    # TODO: Apply after the setup procedure is decoupled from aiohttp
    tracer_provider = TracerProvider(resource=spec.to_resource())
    span_exporter = OTLPSpanExporter(endpoint=spec.endpoint)
    span_processor = BatchSpanProcessor(span_exporter)
    tracer_provider.add_span_processor(span_processor)
    logging.info("OpenTelemetry tracing initialized successfully.")


def instrument_aiohttp_server():
    # TODO: Apply after the setup procedure is decoupled from aiohttp
    AioHttpServerInstrumentor().instrument()
    logging.info("OpenTelemetry tracing for aiohttp server initialized successfully.")


def instrument_aiohttp_client():
    # TODO: Apply after the setup procedure is decoupled from aiohttp
    AioHttpClientInstrumentor().instrument()
    logging.info("OpenTelemetry tracing for aiohttp client initialized successfully.")
