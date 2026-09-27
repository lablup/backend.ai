import logging
import uuid
from collections.abc import Iterator, Sequence
from typing import override

import pytest
from opentelemetry.sdk._logs import ReadableLogRecord
from opentelemetry.sdk._logs.export import (
    LogRecordExporter,
    LogRecordExportResult,
    SimpleLogRecordProcessor,
)

from ai.backend.logging import otel, structured_otel
from ai.backend.logging.otel import OpenTelemetrySpec, apply_otel_loggers
from ai.backend.logging.structured import StructuredLogger
from ai.backend.logging.structured_otel import StructuredOtelLogging
from ai.backend.logging.utils import BraceStyleAdapter

PKG_NS = "tests.logging.otel_pkg"


class _CollectingExporter(LogRecordExporter):
    _records: list[ReadableLogRecord]

    def __init__(self) -> None:
        self._records = []

    @override
    def export(self, batch: Sequence[ReadableLogRecord]) -> LogRecordExportResult:
        self._records.extend(batch)
        return LogRecordExportResult.SUCCESS

    @override
    def shutdown(self) -> None:
        pass

    def delivered(self) -> list[ReadableLogRecord]:
        return list(self._records)


@pytest.fixture
def pkg_logger() -> Iterator[logging.Logger]:
    logger = logging.getLogger(PKG_NS)
    root = logging.getLogger()
    root_handlers, handlers = list(root.handlers), list(logger.handlers)
    propagate, level = logger.propagate, logger.level
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    try:
        yield logger
    finally:
        root.handlers[:] = root_handlers
        logger.handlers[:] = handlers
        logger.propagate, logger.level = propagate, level


@pytest.fixture
def spec() -> OpenTelemetrySpec:
    return OpenTelemetrySpec(
        service_name="test",
        service_version="0.0.0",
        log_level="DEBUG",
        endpoint="http://localhost:4317",
        service_instance_id=uuid.uuid4(),
        service_instance_name="test-0",
        max_queue_size=1,
        max_export_batch_size=1,
    )


@pytest.fixture
def exporter(monkeypatch: pytest.MonkeyPatch) -> _CollectingExporter:
    exporter = _CollectingExporter()
    monkeypatch.setattr(structured_otel, "OTLPLogExporter", lambda endpoint: exporter)
    monkeypatch.setattr(structured_otel, "BatchLogRecordProcessor", SimpleLogRecordProcessor)
    return exporter


@pytest.fixture
def legacy_exporter(monkeypatch: pytest.MonkeyPatch) -> _CollectingExporter:
    exporter = _CollectingExporter()
    monkeypatch.setattr(otel, "OTLPLogExporter", lambda endpoint: exporter)
    monkeypatch.setattr(otel, "BatchLogRecordProcessor", SimpleLogRecordProcessor)
    return exporter


@pytest.fixture
def attached(
    pkg_logger: logging.Logger, exporter: _CollectingExporter, spec: OpenTelemetrySpec
) -> _CollectingExporter:
    StructuredOtelLogging(spec).attach([PKG_NS])
    return exporter


class TestStructuredOtelLogging:
    def test_body_is_message_and_fields_are_attributes(self, attached: _CollectingExporter) -> None:
        StructuredLogger(logging.getLogger(f"{PKG_NS}.structured")).info("x", a=1)

        [record] = attached.delivered()
        assert record.log_record.body == "x"
        assert record.log_record.attributes is not None
        assert record.log_record.attributes["log_tag_a"] == 1

    def test_logger_created_after_attach_reaches_exporter(
        self, attached: _CollectingExporter
    ) -> None:
        name = f"{PKG_NS}.created_after_{uuid.uuid4().hex}"
        assert name not in logging.Logger.manager.loggerDict

        StructuredLogger(logging.getLogger(name)).warning("late")

        [record] = attached.delivered()
        assert record.log_record.body == "late"

    def test_brace_style_records_are_not_delivered(self, attached: _CollectingExporter) -> None:
        BraceStyleAdapter(logging.getLogger(f"{PKG_NS}.brace")).info("started {}", "sess-1")

        assert attached.delivered() == []

    def test_other_handler_formatter_is_kept(
        self,
        pkg_logger: logging.Logger,
        exporter: _CollectingExporter,
        spec: OpenTelemetrySpec,
    ) -> None:
        formatter = logging.Formatter("%(levelname)s %(message)s")
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        pkg_logger.addHandler(console)

        StructuredOtelLogging(spec).attach([PKG_NS])

        assert console.formatter is formatter

    def test_resource_carries_host_name(self, attached: _CollectingExporter) -> None:
        StructuredLogger(logging.getLogger(PKG_NS)).info("resource")

        [record] = attached.delivered()
        assert "host.name" in record.resource.attributes


class TestLegacyOtelLoggers:
    def test_structured_records_are_not_delivered(
        self,
        pkg_logger: logging.Logger,
        legacy_exporter: _CollectingExporter,
        spec: OpenTelemetrySpec,
    ) -> None:
        apply_otel_loggers([pkg_logger], spec)

        StructuredLogger(pkg_logger).info("x", a=1)

        assert legacy_exporter.delivered() == []

    def test_brace_style_records_are_delivered(
        self,
        pkg_logger: logging.Logger,
        legacy_exporter: _CollectingExporter,
        spec: OpenTelemetrySpec,
    ) -> None:
        apply_otel_loggers([pkg_logger], spec)

        BraceStyleAdapter(pkg_logger).info("started {}", "sess-1")

        assert len(legacy_exporter.delivered()) == 1
