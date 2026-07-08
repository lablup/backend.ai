"""Guard: owner_access_key is rejected whenever the X-BackendAI-Act-As header is
present (BEP-1058 §4.4), regardless of the value — self-impersonation included.

The check lives at the owner_access_key consumers (and the delegation
authorization site), not in the auth middleware — the middleware must not
inspect per-endpoint request bodies.
"""

from __future__ import annotations

import pytest

from ai.backend.common.contexts.user import with_impersonation
from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.utils import (
    check_if_requester_is_eligible_to_act_as_target_user,
    reject_owner_access_key_while_impersonating,
)


def test_owner_access_key_rejected_while_impersonating() -> None:
    with with_impersonation():
        with pytest.raises(InvalidAPIParameters):
            reject_owner_access_key_while_impersonating("AKIAOWNER")


def test_owner_access_key_rejected_even_for_self_impersonation() -> None:
    # The caller's own key is still rejected: the header presence is what matters.
    with with_impersonation():
        with pytest.raises(InvalidAPIParameters):
            reject_owner_access_key_while_impersonating("AKIACALLER")


def test_none_owner_access_key_is_noop_while_impersonating() -> None:
    with with_impersonation():
        reject_owner_access_key_while_impersonating(None)


def test_owner_access_key_allowed_when_not_impersonating() -> None:
    reject_owner_access_key_while_impersonating("AKIAOWNER")


def test_eligibility_check_rejected_while_impersonating() -> None:
    with with_impersonation():
        with pytest.raises(InvalidAPIParameters):
            check_if_requester_is_eligible_to_act_as_target_user(
                UserRole.SUPERADMIN, "default", UserRole.USER, "default"
            )


def test_eligibility_check_allowed_when_not_impersonating() -> None:
    assert check_if_requester_is_eligible_to_act_as_target_user(
        UserRole.SUPERADMIN, "default", UserRole.USER, "default"
    )
