"""RBAC scope targeting and authorization for EnqueueSessionAction owner delegation.

When a session is enqueued on behalf of another user (``owner_id`` set), the
RBAC scope must target the *owner's* USER scope so the validator authorizes the
caller against the owner rather than against the caller's own scope (which would
always pass and leave delegation unguarded). The permission lookup itself is the
repository's job, so the authorization tests mock it and only assert which scope
the validator asks about and how the verdict propagates.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.identifier.user import UserID
from ai.backend.common.types import SessionTypes
from ai.backend.manager.actions.action.base import BaseActionTriggerMeta
from ai.backend.manager.actions.validators.rbac.scope import ScopeActionRBACValidator
from ai.backend.manager.data.permission.role import ScopeChainPermissionCheckInput
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.manager.services.session.actions.enqueue_session import (
    EnqueueSessionAction,
    ResourceSlotEntry,
    SessionResourceSpec,
    SessionSchedulingSpec,
)


def _make_action(
    *,
    user_id: UserID,
    owner_id: UserID | None,
) -> EnqueueSessionAction:
    return EnqueueSessionAction(
        session_name="test-session",
        session_type=SessionTypes.INTERACTIVE,
        image_id=uuid.uuid4(),
        resource=SessionResourceSpec(
            entries=[ResourceSlotEntry(resource_type="cpu", quantity="1")],
        ),
        scheduling=SessionSchedulingSpec(),
        user_id=user_id,
        owner_id=owner_id,
    )


def _non_admin(user_id: UserID) -> UserData:
    return UserData(
        user_id=user_id,
        is_authorized=True,
        is_admin=False,
        is_superadmin=False,
        role=UserRole.USER,
        domain_name="default",
    )


@pytest.fixture
def trigger_meta() -> BaseActionTriggerMeta:
    return BaseActionTriggerMeta(action_id=uuid.uuid4(), started_at=datetime.now(UTC))


class TestEnqueueSessionActionDelegationScope:
    @pytest.mark.parametrize(
        "delegated",
        [False, True],
        ids=[
            "no_owner_id_falls_back_to_caller_scope",
            "owner_id_delegates_to_owner_scope",
        ],
    )
    def test_rbac_scope_targets_owner_when_delegating(self, delegated: bool) -> None:
        caller_id = UserID(uuid.uuid4())
        owner_id = UserID(uuid.uuid4())
        action = _make_action(
            user_id=caller_id,
            owner_id=owner_id if delegated else None,
        )
        # Delegation must authorize against the owner, never the caller.
        expected_id = owner_id if delegated else caller_id

        assert action.scope_id() == str(expected_id)
        target = action.target_element()
        assert target.element_type == RBACElementType.USER
        assert target.element_id == str(expected_id)


class TestEnqueueSessionDelegationAuthorization:
    async def test_delegation_authorizes_against_owner_scope(
        self,
        trigger_meta: BaseActionTriggerMeta,
    ) -> None:
        caller_id = UserID(uuid.uuid4())
        owner_id = UserID(uuid.uuid4())
        repository = AsyncMock(spec=PermissionControllerRepository)
        repository.check_permission_with_scope_chain.return_value = True
        validator = ScopeActionRBACValidator(repository, MagicMock())

        action = _make_action(user_id=caller_id, owner_id=owner_id)
        with with_user(_non_admin(caller_id)):
            await validator.validate(action, trigger_meta)

        # The permission check must target the owner's USER scope, not the caller's.
        repository.check_permission_with_scope_chain.assert_awaited_once()
        checked: ScopeChainPermissionCheckInput = (
            repository.check_permission_with_scope_chain.await_args.args[0]
        )
        assert checked.key.user_id == caller_id
        assert checked.key.element_type == RBACElementType.USER
        assert checked.key.entity_id == str(owner_id)

    async def test_denied_delegation_raises(
        self,
        trigger_meta: BaseActionTriggerMeta,
    ) -> None:
        caller_id = UserID(uuid.uuid4())
        owner_id = UserID(uuid.uuid4())
        repository = AsyncMock(spec=PermissionControllerRepository)
        repository.check_permission_with_scope_chain.return_value = False
        validator = ScopeActionRBACValidator(repository, MagicMock())

        action = _make_action(user_id=caller_id, owner_id=owner_id)
        with with_user(_non_admin(caller_id)):
            with pytest.raises(NotEnoughPermission):
                await validator.validate(action, trigger_meta)
