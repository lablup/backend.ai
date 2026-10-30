from __future__ import annotations

import logging
import uuid
from collections.abc import Iterator

import pytest

from ai.backend.common.contexts.user import current_user, triggered_user, with_user_context
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.logging.structured import StructuredLogger

LOGGER_NAME = "tests.common.contexts.user"


def _user(role: UserRole = UserRole.USER) -> UserData:
    return UserData(
        user_id=uuid.uuid4(),
        is_authorized=True,
        is_admin=role in (UserRole.ADMIN, UserRole.SUPERADMIN),
        is_superadmin=role == UserRole.SUPERADMIN,
        role=role,
        domain_name="default",
        domain_id=DomainID(uuid.uuid4()),
    )


@pytest.fixture
def log() -> StructuredLogger:
    return StructuredLogger(logging.getLogger(LOGGER_NAME))


@pytest.fixture
def capture(caplog: pytest.LogCaptureFixture) -> Iterator[pytest.LogCaptureFixture]:
    with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
        yield caplog


def test_users_are_none_when_unset() -> None:
    assert current_user() is None
    assert triggered_user() is None


def test_same_user_logs_user_id_only(
    log: StructuredLogger, capture: pytest.LogCaptureFixture
) -> None:
    user = _user()
    with with_user_context(user, user):
        assert current_user() == user
        assert triggered_user() == user
        log.info("inside")

    record = capture.records[0]
    assert record.__dict__["log_tag_user_id"] == str(user.user_id)
    assert "log_tag_triggered_user_id" not in record.__dict__
    assert current_user() is None
    assert triggered_user() is None


def test_acting_as_another_user_sets_and_logs_both(
    log: StructuredLogger, capture: pytest.LogCaptureFixture
) -> None:
    effective = _user()
    trigger = _user(UserRole.SUPERADMIN)
    with with_user_context(effective, trigger):
        assert current_user() == effective
        assert triggered_user() == trigger
        log.info("inside")

    record = capture.records[0]
    assert record.__dict__["log_tag_user_id"] == str(effective.user_id)
    assert record.__dict__["log_tag_triggered_user_id"] == str(trigger.user_id)
    assert current_user() is None
    assert triggered_user() is None


def test_effective_user_alone_leaves_trigger_unset() -> None:
    user = _user()
    with with_user_context(user):
        assert current_user() == user
        assert triggered_user() is None


def test_no_user_sets_nothing(log: StructuredLogger, capture: pytest.LogCaptureFixture) -> None:
    with with_user_context(None, None):
        assert current_user() is None
        assert triggered_user() is None
        log.info("inside")

    assert "log_tag_user_id" not in capture.records[0].__dict__


def test_nested_context_restores_previous() -> None:
    outer = _user()
    inner = _user(UserRole.ADMIN)
    with with_user_context(outer, outer):
        with with_user_context(inner, inner):
            assert current_user() == inner
            assert triggered_user() == inner
        assert current_user() == outer
        assert triggered_user() == outer
