"""Tests for ``AssignUserIdentityRule``."""

from __future__ import annotations

import uuid

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.manager.data.session.draft import (
    SessionIdentityDraft,
    SessionSpecDraft,
)
from ai.backend.manager.data.session.options import DefaultSessionOptions
from ai.backend.manager.sokovan.scheduling_controller.preparers.assign_user_identity_rule import (
    AssignUserIdentityRule,
)
from ai.backend.manager.sokovan.scheduling_controller.preparers.draft_rule import (
    SessionSpecPreparationContext,
)


@pytest.fixture
def rule() -> AssignUserIdentityRule:
    return AssignUserIdentityRule()


@pytest.fixture
def context() -> SessionSpecPreparationContext:
    return SessionSpecPreparationContext(
        resource_group_defaults=DefaultSessionOptions(),
    )


def _user(user_id: uuid.UUID) -> UserData:
    return UserData(
        user_id=user_id,
        is_authorized=True,
        is_admin=False,
        is_superadmin=False,
        role=UserRole.USER,
        domain_name="default",
    )


class TestAssignUserIdentityRule:
    async def test_fills_user_uuid_from_current_user(
        self,
        rule: AssignUserIdentityRule,
        context: SessionSpecPreparationContext,
    ) -> None:
        creator = uuid.uuid4()
        with with_user(_user(creator)):
            result = await rule.prepare(SessionSpecDraft(), context)
        assert result.identity.user_uuid == creator

    async def test_preserves_caller_user_uuid(
        self,
        rule: AssignUserIdentityRule,
        context: SessionSpecPreparationContext,
    ) -> None:
        """Defensive: if the draft already has user_uuid, the rule is a no-op."""
        prefilled = uuid.uuid4()
        draft = SessionSpecDraft(
            identity=SessionIdentityDraft(user_uuid=prefilled),
        )
        with with_user(_user(uuid.uuid4())):
            result = await rule.prepare(draft, context)
        assert result.identity.user_uuid == prefilled

    async def test_noop_when_no_current_user(
        self,
        rule: AssignUserIdentityRule,
        context: SessionSpecPreparationContext,
    ) -> None:
        # No with_user block — ambient ctx is empty.
        result = await rule.prepare(SessionSpecDraft(), context)
        assert result.identity.user_uuid is None
