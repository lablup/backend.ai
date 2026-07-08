from __future__ import annotations

import uuid

from ai.backend.common.contexts.user import (
    current_user,
    triggered_user,
    with_triggered_user,
    with_user,
)
from ai.backend.common.data.user.types import UserData, UserRole


def test_triggered_user_none_when_unset() -> None:
    assert triggered_user() is None


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
