from __future__ import annotations

import uuid

from ai.backend.common.contexts.user import (
    current_user,
    is_impersonating,
    triggered_user,
    with_triggered_user,
    with_user,
)
from ai.backend.common.data.user.types import UserData, UserRole


def _user(is_superadmin: bool = False) -> UserData:
    return UserData(
        user_id=uuid.uuid4(),
        is_authorized=True,
        is_admin=is_superadmin,
        is_superadmin=is_superadmin,
        role=UserRole.SUPERADMIN if is_superadmin else UserRole.USER,
        domain_name="default",
    )


def test_triggered_user_none_when_unset() -> None:
    assert triggered_user() is None


def test_is_impersonating_true_when_trigger_differs_from_effective() -> None:
    target = _user()
    super_admin = _user(is_superadmin=True)
    with with_user(target), with_triggered_user(super_admin):
        assert is_impersonating() is True


def test_is_impersonating_false_when_trigger_equals_effective() -> None:
    user = _user()
    with with_user(user), with_triggered_user(user):
        assert is_impersonating() is False


def test_is_impersonating_false_when_context_unset() -> None:
    assert is_impersonating() is False
    with with_user(_user()):
        # Only the effective user is set (no trigger) — not impersonation.
        assert is_impersonating() is False


def test_triggered_user_inside_context() -> None:
    user = UserData(
        user_id=uuid.uuid4(),
        is_authorized=True,
        is_admin=False,
        is_superadmin=False,
        role=UserRole.USER,
        domain_name="default",
    )
    with with_triggered_user(user):
        assert triggered_user() == user
    assert triggered_user() is None


def test_current_and_triggered_are_independent() -> None:
    effective = UserData(
        user_id=uuid.uuid4(),
        is_authorized=True,
        is_admin=False,
        is_superadmin=False,
        role=UserRole.USER,
        domain_name="default",
    )
    trigger = UserData(
        user_id=uuid.uuid4(),
        is_authorized=True,
        is_admin=True,
        is_superadmin=True,
        role=UserRole.SUPERADMIN,
        domain_name="default",
    )
    with with_user(effective), with_triggered_user(trigger):
        assert current_user() == effective
        assert triggered_user() == trigger
    assert current_user() is None
    assert triggered_user() is None


def test_nested_triggered_user_restores_previous() -> None:
    outer = UserData(
        user_id=uuid.uuid4(),
        is_authorized=True,
        is_admin=False,
        is_superadmin=False,
        role=UserRole.USER,
        domain_name="default",
    )
    inner = UserData(
        user_id=uuid.uuid4(),
        is_authorized=True,
        is_admin=True,
        is_superadmin=False,
        role=UserRole.ADMIN,
        domain_name="default",
    )
    with with_triggered_user(outer):
        assert triggered_user() == outer
        with with_triggered_user(inner):
            assert triggered_user() == inner
        assert triggered_user() == outer
