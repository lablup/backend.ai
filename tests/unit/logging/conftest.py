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
        logger.warning("image pull retried", attempt=3)
    [record] = caplog.records
    return record


@pytest.fixture
def structured_exception_record(caplog: pytest.LogCaptureFixture) -> logging.LogRecord:
    logger = StructuredLogger(logging.getLogger(_RECORD_LOGGER_NAME))
    with caplog.at_level(logging.INFO, logger=_RECORD_LOGGER_NAME):
        try:
            _ = 1 / 0
        except ZeroDivisionError:
            logger.exception("kernel creation failed", kernel_id="kernel-1")
    [record] = caplog.records
    return record


@pytest.fixture
def record_with_plain_extra(caplog: pytest.LogCaptureFixture) -> logging.LogRecord:
    with caplog.at_level(logging.INFO, logger=_RECORD_LOGGER_NAME):
        logging.getLogger(_RECORD_LOGGER_NAME).info(
            "request %s handled", "GET /", extra={"user_id": "user-1", "email": "a@example.com"}
        )
    [record] = caplog.records
    return record
