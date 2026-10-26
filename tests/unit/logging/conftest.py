import logging

import pytest

from ai.backend.logging.structured import StructuredLogger, with_log_context

pytest_plugins = [
    "ai.backend.testutils.otel",
]

_RECORD_LOGGER_NAME = "tests.logging.records"


@pytest.fixture
def structured_record(caplog: pytest.LogCaptureFixture) -> logging.LogRecord:
    logger = StructuredLogger(logging.getLogger(_RECORD_LOGGER_NAME))
    with (
        caplog.at_level(logging.INFO, logger=_RECORD_LOGGER_NAME),
        with_log_context(kernel_id="kernel-1"),
    ):
        logger.warning("mock error", attempt=3)
    [record] = caplog.records
    return record
