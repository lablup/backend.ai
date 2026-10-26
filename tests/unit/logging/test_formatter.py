import logging
import re

import pytest

from ai.backend.logging.formatter import ColorizedFormatter, ConsoleFormatter

_ANSI_ESCAPE_SEQUENCE = re.compile(r"\x1b\[[0-9;]*m")


@pytest.fixture(
    params=[ConsoleFormatter, ColorizedFormatter],
    ids=lambda formatter_class: formatter_class.__name__,
)
def console_formatter(request: pytest.FixtureRequest) -> logging.Formatter:
    formatter_class: type[logging.Formatter] = request.param
    return formatter_class("%(message)s")


class TestConsoleFormatters:
    def test_fields_follow_message(
        self, console_formatter: logging.Formatter, structured_record: logging.LogRecord
    ) -> None:
        console_line = _ANSI_ESCAPE_SEQUENCE.sub("", console_formatter.format(structured_record))

        assert console_line == "mock error message context_field=context-value call_field=1"
