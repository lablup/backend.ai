from __future__ import annotations

import uuid

from ai.backend.common.contexts.user import (
    current_user,
    triggered_user,
    with_triggered_user,
    with_user,
)
from ai.backend.common.data.user.types import UserData, UserRole


def _user(role: UserRole = UserRole.USER) -> UserData:
    return UserData(
        user_id=uuid.uuid4(),
        is_authorized=True,
        is_admin=role in (UserRole.ADMIN, UserRole.SUPERADMIN),
        is_superadmin=role == UserRole.SUPERADMIN,
        role=role,
        domain_name="default",
    )


def test_triggered_user_none_when_unset() -> None:
    assert triggered_user() is None


def test_triggered_user_inside_context() -> None:
    user = _user()
    with with_triggered_user(user):
        assert triggered_user() == user
    assert triggered_user() is None


def test_current_and_triggered_are_independent() -> None:
    effective = _user()
    trigger = _user(UserRole.SUPERADMIN)
    with with_user(effective), with_triggered_user(trigger):
        assert current_user() == effective
        assert triggered_user() == trigger
    assert current_user() is None
    assert triggered_user() is None


def test_nested_triggered_user_restores_previous() -> None:
    outer = _user()
    inner = _user(UserRole.ADMIN)
    with with_triggered_user(outer):
        assert triggered_user() == outer
        with with_triggered_user(inner):
            assert triggered_user() == inner
        assert triggered_user() == outer
