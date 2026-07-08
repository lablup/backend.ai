"""Guard: owner_access_key delegation is rejected while impersonating (BEP-1058 §4.4).

The check lives at the delegation authorization site
(``check_if_requester_is_eligible_to_act_as_target_user``), not in the auth
middleware — the middleware must not inspect per-endpoint request bodies.
"""

from __future__ import annotations

import uuid

import pytest

from ai.backend.common.contexts.user import with_triggered_user, with_user
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.utils import check_if_requester_is_eligible_to_act_as_target_user


def _user(role: UserRole = UserRole.USER, user_id: uuid.UUID | None = None) -> UserData:
    return UserData(
        user_id=user_id or uuid.uuid4(),
        is_authorized=True,
        is_admin=role in (UserRole.ADMIN, UserRole.SUPERADMIN),
        is_superadmin=role == UserRole.SUPERADMIN,
        role=role,
        domain_name="default",
    )


def test_owner_access_key_rejected_while_impersonating() -> None:
    effective = _user(UserRole.USER)  # target
    trigger = _user(UserRole.SUPERADMIN)  # super admin caller
    with with_user(effective), with_triggered_user(trigger):
        with pytest.raises(InvalidAPIParameters):
            check_if_requester_is_eligible_to_act_as_target_user(
                UserRole.SUPERADMIN, "default", UserRole.USER, "default"
            )


def test_owner_access_key_allowed_when_not_impersonating() -> None:
    same = _user(UserRole.SUPERADMIN)
    with with_user(same), with_triggered_user(same):
        assert check_if_requester_is_eligible_to_act_as_target_user(
            UserRole.SUPERADMIN, "default", UserRole.USER, "default"
        )


def test_owner_access_key_allowed_without_user_context() -> None:
    assert check_if_requester_is_eligible_to_act_as_target_user(
        UserRole.SUPERADMIN, "default", UserRole.USER, "default"
    )
