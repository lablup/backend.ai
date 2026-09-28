import logging
import socket
from collections.abc import Iterable

from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource

from ai.backend.logging.otel import OpenTelemetrySpec
from ai.backend.logging.structured import StructuredMessage

__all__ = ("StructuredOtelLogging",)


class StructuredOtelLogging:
    _spec: OpenTelemetrySpec

    def __init__(self, spec: OpenTelemetrySpec) -> None:
        self._spec = spec

    def attach(self, pkg_ns: Iterable[str]) -> None:
        # The pkg-ns loggers do not propagate, so each of them and the root needs the handler.
        handler = self._create_handler()
        for name in {"", *pkg_ns}:
            logging.getLogger(name).addHandler(handler)

    def _create_handler(self) -> LoggingHandler:
        resource = self._spec.to_resource().merge(Resource({"host.name": socket.gethostname()}))
        log_provider = LoggerProvider(resource=resource)
        log_provider.add_log_record_processor(
            BatchLogRecordProcessor(OTLPLogExporter(endpoint=self._spec.endpoint))
        )
        log_level = logging.getLevelNamesMapping().get(self._spec.log_level.upper(), logging.INFO)
        handler = LoggingHandler(level=log_level, logger_provider=log_provider)
        handler.addFilter(lambda record: isinstance(record.msg, StructuredMessage))
        return handler
