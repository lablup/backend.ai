import enum
import logging
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, cast, override
from uuid import UUID

import pytest

from ai.backend.logging.structured import StructuredLogger, with_log_context
from ai.backend.logging.utils import BraceStyleAdapter, with_log_context_fields

LOGGER_NAME = "tests.logging.structured"
TRACE_LEVEL = 5


class _Color(enum.StrEnum):
    RED = "red"


class _Priority(enum.IntEnum):
    HIGH = 1


class _UnprintableUUID(UUID):
    @override
    def __str__(self) -> str:
        raise AssertionError("normalized while the level is disabled")


@pytest.fixture
def logger() -> StructuredLogger:
    return StructuredLogger(logging.getLogger(LOGGER_NAME))


@pytest.fixture
def capture_debug(caplog: pytest.LogCaptureFixture) -> Iterator[pytest.LogCaptureFixture]:
    with caplog.at_level(TRACE_LEVEL, logger=LOGGER_NAME):
        yield caplog


@pytest.fixture
def capture_info(caplog: pytest.LogCaptureFixture) -> Iterator[pytest.LogCaptureFixture]:
    with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
        yield caplog


def _record(caplog: pytest.LogCaptureFixture) -> logging.LogRecord:
    assert len(caplog.records) == 1
    return caplog.records[0]


class TestStructuredLogger:
    def test_message_is_kept_and_fields_become_record_attributes(
        self, logger: StructuredLogger, capture_info: pytest.LogCaptureFixture
    ) -> None:
        logger.warning("image pull retried", attempt=3, delay_sec=1.5)

        record = _record(capture_info)
        assert record.getMessage() == "image pull retried"
        assert record.levelno == logging.WARNING
        assert record.__dict__["log_tag_attempt"] == 3
        assert record.__dict__["log_tag_delay_sec"] == 1.5

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (UUID("12345678-1234-5678-1234-567812345678"), "12345678-1234-5678-1234-567812345678"),
            (_Color.RED, "red"),
            (_Priority.HIGH, 1),
            (Path("/tmp/vfolder"), "/tmp/vfolder"),
            (Decimal("1.50"), "1.50"),
            (datetime(2026, 9, 27, 12, 0, tzinfo=UTC), "2026-09-27T12:00:00+00:00"),
            ("plain", "plain"),
            (None, None),
        ],
    )
    def test_values_are_normalized(
        self,
        logger: StructuredLogger,
        capture_info: pytest.LogCaptureFixture,
        value: Any,
        expected: Any,
    ) -> None:
        logger.info("value logged", field_value=value)

        field_value = _record(capture_info).__dict__["log_tag_field_value"]
        assert field_value == expected
        assert type(field_value) is type(expected)

    @pytest.mark.parametrize("name", ["name", "module", "message", "asctime", "msg", "args"])
    def test_log_record_attribute_names_are_prefixed(
        self, logger: StructuredLogger, capture_info: pytest.LogCaptureFixture, name: str
    ) -> None:
        log_info = cast(Callable[..., None], logger.info)
        log_info("reserved name logged", **{name: "value"})

        record = _record(capture_info)
        assert record.getMessage() == "reserved name logged"
        assert record.__dict__[f"log_tag_{name}"] == "value"
        assert record.name == LOGGER_NAME

    def test_call_field_overrides_context_field(
        self, logger: StructuredLogger, capture_info: pytest.LogCaptureFixture
    ) -> None:
        with with_log_context(session_id="outer", kernel_id="kernel"):
            logger.info("session scheduled", session_id="call")

        record = _record(capture_info)
        assert record.__dict__["log_tag_session_id"] == "call"
        assert record.__dict__["log_tag_kernel_id"] == "kernel"

    def test_disabled_level_skips_normalization(
        self, logger: StructuredLogger, capture_info: pytest.LogCaptureFixture
    ) -> None:
        logger.debug("allocation candidates", resource_group_id=_UnprintableUUID(int=1))

        assert capture_info.records == []

    @pytest.mark.parametrize(
        ("method_name", "level"), [("debug", logging.DEBUG), ("trace", TRACE_LEVEL)]
    )
    def test_debug_and_trace_format_positional_args(
        self,
        logger: StructuredLogger,
        capture_debug: pytest.LogCaptureFixture,
        method_name: str,
        level: int,
    ) -> None:
        log_method = getattr(logger, method_name)
        log_method("allocation candidates: {} of {}", 2, 5, resource_group_id="rg")

        record = _record(capture_debug)
        assert record.levelno == level
        assert record.getMessage() == "allocation candidates: 2 of 5"
        assert record.__dict__["log_tag_resource_group_id"] == "rg"

    @pytest.mark.parametrize("method_name", ["info", "warning", "error", "exception"])
    def test_info_and_above_reject_positional_args(
        self, logger: StructuredLogger, capture_info: pytest.LogCaptureFixture, method_name: str
    ) -> None:
        log_method = cast(Callable[..., None], getattr(logger, method_name))

        with pytest.raises(TypeError):
            log_method("kernel {} created", "kernel-1")
        assert capture_info.records == []

    def test_exception_carries_traceback(
        self, logger: StructuredLogger, capture_info: pytest.LogCaptureFixture
    ) -> None:
        try:
            _ = 1 / 0
        except ZeroDivisionError:
            logger.exception("kernel creation failed", kernel_id="kernel-1")

        record = _record(capture_info)
        assert record.levelno == logging.ERROR
        assert record.exc_info is not None
        assert record.exc_info[0] is ZeroDivisionError
        assert record.__dict__["log_tag_kernel_id"] == "kernel-1"
        assert "Traceback (most recent call last):" in capture_info.text

    def test_stacklevel_points_at_caller(
        self, logger: StructuredLogger, capture_info: pytest.LogCaptureFixture
    ) -> None:
        logger.info("caller located")

        record = _record(capture_info)
        assert record.funcName == "test_stacklevel_points_at_caller"
        assert record.pathname == __file__

    def test_stacklevel_skips_wrapper_frames(
        self, logger: StructuredLogger, capture_info: pytest.LogCaptureFixture
    ) -> None:
        def wrapper() -> None:
            logger.info("wrapper caller located", stacklevel=2)

        wrapper()

        assert _record(capture_info).funcName == "test_stacklevel_skips_wrapper_frames"


class TestWithLogContext:
    def test_fields_apply_only_inside_scope(
        self, logger: StructuredLogger, capture_info: pytest.LogCaptureFixture
    ) -> None:
        with with_log_context(action_id="action-1"):
            logger.info("inside scope")
        logger.info("outside scope")

        inside, outside = capture_info.records
        assert inside.__dict__["log_tag_action_id"] == "action-1"
        assert not hasattr(outside, "log_tag_action_id")

    def test_nested_scopes_merge_and_inner_wins(
        self, logger: StructuredLogger, capture_info: pytest.LogCaptureFixture
    ) -> None:
        with with_log_context(action_id="outer", action_name="create"):
            with with_log_context(action_id="inner"):
                logger.info("inner scope")
            logger.info("outer scope")

        inner, outer = (record.__dict__ for record in capture_info.records)
        assert inner["log_tag_action_id"] == "inner"
        assert inner["log_tag_action_name"] == "create"
        assert outer["log_tag_action_id"] == "outer"
        assert outer["log_tag_action_name"] == "create"

    def test_values_and_names_are_normalized(
        self, logger: StructuredLogger, capture_info: pytest.LogCaptureFixture
    ) -> None:
        session_id = UUID("12345678-1234-5678-1234-567812345678")
        with with_log_context(session_id=session_id, color=_Color.RED, module="scheduler"):
            logger.info("scope normalized")

        record = _record(capture_info)
        assert record.__dict__["log_tag_session_id"] == str(session_id)
        assert record.__dict__["log_tag_color"] == "red"
        assert record.__dict__["log_tag_module"] == "scheduler"
        assert record.module == "test_structured"


class TestIsolationFromBraceStyleAdapter:
    def test_adapter_ignores_log_context(self, capture_info: pytest.LogCaptureFixture) -> None:
        adapter = BraceStyleAdapter(logging.getLogger(LOGGER_NAME))
        with with_log_context(request_id="req-1"):
            adapter.info("request {} handled", "GET /")

        record = _record(capture_info)
        assert not hasattr(record, "log_tag_request_id")
        assert not hasattr(record, "request_id")

    def test_logger_ignores_legacy_context_fields(
        self, logger: StructuredLogger, capture_info: pytest.LogCaptureFixture
    ) -> None:
        with with_log_context_fields({"user_id": "user-1"}):
            logger.info("legacy scope")

        record = _record(capture_info)
        assert not hasattr(record, "user_id")
        assert not hasattr(record, "log_tag_user_id")
