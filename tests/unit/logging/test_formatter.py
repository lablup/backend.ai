import logging
import re
from dataclasses import dataclass

import pytest

from ai.backend.logging.formatter import ColorizedFormatter, ConsoleFormatter

_ANSI_ESCAPE_SEQUENCE = re.compile(r"\x1b\[[0-9;]*m")


@dataclass(frozen=True)
class _FieldValueCase:
    value: str | int | float | bool | None
    rendered: str


@pytest.fixture(
    params=[ConsoleFormatter, ColorizedFormatter],
    ids=lambda formatter_class: formatter_class.__name__,
)
def console_formatter(request: pytest.FixtureRequest) -> logging.Formatter:
    formatter_class: type[logging.Formatter] = request.param
    return formatter_class("%(message)s")


@pytest.fixture
def record_with_field_value(case: _FieldValueCase) -> logging.LogRecord:
    return logging.makeLogRecord({"msg": "value logged", "log_tag_field_value": case.value})


class TestConsoleFormatters:
    def test_fields_follow_message(
        self, console_formatter: logging.Formatter, structured_record: logging.LogRecord
    ) -> None:
        console_line = _ANSI_ESCAPE_SEQUENCE.sub("", console_formatter.format(structured_record))

        assert console_line == "image pull retried kernel_id=kernel-1 attempt=3"

    def test_plain_extra_line_is_unchanged(
        self, console_formatter: logging.Formatter, record_with_plain_extra: logging.LogRecord
    ) -> None:
        console_line = _ANSI_ESCAPE_SEQUENCE.sub(
            "", console_formatter.format(record_with_plain_extra)
        )

        assert console_line == "request GET / handled"

    def test_traceback_follows_fields_line(
        self,
        console_formatter: logging.Formatter,
        structured_exception_record: logging.LogRecord,
    ) -> None:
        formatted_record = console_formatter.format(structured_exception_record)

        first_line, traceback_text = _ANSI_ESCAPE_SEQUENCE.sub("", formatted_record).split("\n", 1)
        assert first_line == "kernel creation failed kernel_id=kernel-1"
        assert traceback_text.startswith("Traceback (most recent call last):")

    @pytest.mark.parametrize(
        "case",
        [
            _FieldValueCase(value="kernel-1", rendered="kernel-1"),
            _FieldValueCase(value="Python 3.13 (env: /opt)", rendered='"Python 3.13 (env: /opt)"'),
            _FieldValueCase(value="a=b", rendered='"a=b"'),
            _FieldValueCase(value='"quoted"', rendered='"\\"quoted\\""'),
            _FieldValueCase(value="", rendered='""'),
            _FieldValueCase(value=3, rendered="3"),
            _FieldValueCase(value=1.5, rendered="1.5"),
            _FieldValueCase(value=True, rendered="True"),
            _FieldValueCase(value=None, rendered="None"),
        ],
        ids=lambda case: repr(case.value),
    )
    def test_field_values_are_rendered(
        self,
        console_formatter: logging.Formatter,
        record_with_field_value: logging.LogRecord,
        case: _FieldValueCase,
    ) -> None:
        console_line = _ANSI_ESCAPE_SEQUENCE.sub(
            "", console_formatter.format(record_with_field_value)
        )

        assert console_line == f"value logged field_value={case.rendered}"
