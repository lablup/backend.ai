import logging
import uuid

import pytest

from ai.backend.logging import BraceStyleAdapter, otel
from ai.backend.logging.otel import LegacyOtelLogging, OpenTelemetrySpec
from ai.backend.logging.structured import StructuredLogger, with_log_context
from ai.backend.logging.utils import with_log_context_fields


def _adapter(logger: logging.Logger) -> BraceStyleAdapter:
    with pytest.warns(DeprecationWarning, match="BraceStyleAdapter"):
        return BraceStyleAdapter(logger)


def test_brace_style_adapter_warns_on_construction() -> None:
    with pytest.warns(DeprecationWarning, match="StructuredLogger") as record:
        BraceStyleAdapter(logging.getLogger())

    assert record[0].filename == __file__


def test_with_log_context_fields_warns_on_enter() -> None:
    with (
        pytest.warns(DeprecationWarning, match="with_log_context") as record,
        with_log_context_fields({"user": "Alice"}),
    ):
        pass

    assert record[0].filename == __file__


def test_brace_style_adapter_positional_args(caplog: pytest.LogCaptureFixture) -> None:
    logger = _adapter(logging.getLogger())
    with caplog.at_level(logging.INFO):
        logger.info("Hello, {}!", "World")
        logger.info("Hello, {1} {0}!", "foo", "bar")

    assert caplog.record_tuples == [
        ("root", logging.INFO, "Hello, World!"),
        ("root", logging.INFO, "Hello, bar foo!"),
    ]


def test_brace_style_adapter_custom_kwargs(caplog: pytest.LogCaptureFixture) -> None:
    logger = _adapter(logging.getLogger())
    with caplog.at_level(logging.INFO):
        logger.info("Hello, {name}!", name="World")
    assert caplog.record_tuples == [
        ("root", logging.INFO, "Hello, World!"),
    ]

    with pytest.raises(KeyError):
        # System-level context kwargs are hidden.
        with caplog.at_level(logging.INFO):
            logger.info("Hello, {stacklevel}!", stacklevel=0)


def test_brace_style_adapter_exceptions(caplog: pytest.LogCaptureFixture) -> None:
    logger = _adapter(logging.getLogger())
    with caplog.at_level(logging.ERROR):
        try:
            _ = 1 / 0
        except ZeroDivisionError:
            logger.exception("Oops! {detail}", detail="big mistake")

    assert caplog.record_tuples == [("root", logging.ERROR, "Oops! big mistake")]
    assert "Traceback (most recent call last):" in caplog.text


def test_brace_style_adapter_context_fields_via_extra(caplog: pytest.LogCaptureFixture) -> None:
    logger = _adapter(logging.getLogger())
    with (
        pytest.warns(DeprecationWarning),
        with_log_context_fields({"user": "Alice"}),
        caplog.at_level(logging.INFO),
    ):
        logger.info("Hello, {extra[user]} {extra[email]}!", extra={"email": "alice@example.com"})

    assert caplog.record_tuples == [("root", logging.INFO, "Hello, Alice alice@example.com!")]


def test_brace_style_adapter_formatting(caplog: pytest.LogCaptureFixture) -> None:
    logger = _adapter(logging.getLogger())
    with caplog.at_level(logging.INFO):
        logger.info("Hello, {!r}!", "World")
        logger.info("Hello, {:.2f}!", 0.123)
        logger.info("Hello, {name!r}!", name="Earth")
        logger.info("Hello, {value:.2f}!", value=0.567)

    assert caplog.record_tuples == [
        ("root", logging.INFO, "Hello, 'World'!"),
        ("root", logging.INFO, "Hello, 0.12!"),
        ("root", logging.INFO, "Hello, 'Earth'!"),
        ("root", logging.INFO, "Hello, 0.57!"),
    ]


def test_brace_style_adapter_ignores_log_context(caplog: pytest.LogCaptureFixture) -> None:
    adapter = _adapter(logging.getLogger())
    with caplog.at_level(logging.INFO), with_log_context(request_id="req-1"):
        adapter.info("request {} handled", "GET /")

    [record] = caplog.records
    assert not hasattr(record, "log_tag_request_id")
    assert not hasattr(record, "request_id")


def test_structured_logger_ignores_legacy_context_fields(
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger = StructuredLogger(logging.getLogger())
    with (
        pytest.warns(DeprecationWarning),
        with_log_context_fields({"user_id": "user-1"}),
        caplog.at_level(logging.INFO),
    ):
        logger.info("legacy scope")

    [record] = caplog.records
    assert not hasattr(record, "user_id")
    assert not hasattr(record, "log_tag_user_id")


def test_adapter_logger_is_attached_to_legacy_otel(monkeypatch: pytest.MonkeyPatch) -> None:
    attached: list[logging.Logger] = []
    monkeypatch.setattr(otel, "apply_otel_loggers", lambda loggers, spec: attached.extend(loggers))
    logger = logging.getLogger(f"tests.logging.adapter.{uuid.uuid4().hex}")
    _adapter(logger)
    spec = OpenTelemetrySpec(
        service_name="test",
        service_version="0.0.0",
        log_level="DEBUG",
        endpoint="http://localhost:4317",
        service_instance_id=uuid.uuid4(),
        service_instance_name="test-0",
        max_queue_size=1,
        max_export_batch_size=1,
    )

    LegacyOtelLogging(spec).attach()

    assert logger in attached
