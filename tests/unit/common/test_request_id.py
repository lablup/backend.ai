import logging
import uuid

import pytest

from ai.backend.common.contexts.request_id import current_request_id, with_request_context
from ai.backend.logging.structured import StructuredLogger

LOGGER_NAME = "tests.common.request_id"


def test_current_request_id_without_context() -> None:
    assert current_request_id() is None


def test_given_request_id_is_set_on_both(caplog: pytest.LogCaptureFixture) -> None:
    log = StructuredLogger(logging.getLogger(LOGGER_NAME))
    test_id = str(uuid.uuid4())
    with caplog.at_level(logging.INFO, logger=LOGGER_NAME), with_request_context(test_id):
        assert current_request_id() == test_id
        log.info("inside")

    assert caplog.records[0].__dict__["log_tag_request_id"] == test_id
    assert current_request_id() is None


def test_generated_request_id_is_the_same_on_both(caplog: pytest.LogCaptureFixture) -> None:
    log = StructuredLogger(logging.getLogger(LOGGER_NAME))
    with caplog.at_level(logging.INFO, logger=LOGGER_NAME), with_request_context():
        request_id = current_request_id()
        log.info("inside")

    assert request_id is not None
    uuid.UUID(request_id)
    assert caplog.records[0].__dict__["log_tag_request_id"] == request_id
    assert current_request_id() is None


def test_nested_request_contexts() -> None:
    outer_id = str(uuid.uuid4())
    inner_id = str(uuid.uuid4())

    with with_request_context(outer_id):
        assert current_request_id() == outer_id
        with with_request_context(inner_id):
            assert current_request_id() == inner_id
        assert current_request_id() == outer_id
    assert current_request_id() is None
