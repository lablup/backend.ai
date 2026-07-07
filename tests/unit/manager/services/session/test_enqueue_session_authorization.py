"""RBAC authorization of EnqueueSessionAction owner delegation.

When a session is enqueued on behalf of another user (``owner_id`` set), the
scope validator must authorize the caller against the *owner's* USER scope, and
propagate a denial as ``NotEnoughPermission``. The permission lookup itself is
the repository's job, so it is mocked here — this test only asserts which scope
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


def _make_action(*, caller_id: UserID, owner_id: UserID | None) -> EnqueueSessionAction:
    return EnqueueSessionAction(
        session_name="delegation-test",
        session_type=SessionTypes.INTERACTIVE,
        image_id=uuid.uuid4(),
        resource=SessionResourceSpec(
            entries=[ResourceSlotEntry(resource_type="cpu", quantity="1")],
        ),
        scheduling=SessionSchedulingSpec(),
        user_id=caller_id,
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

        action = _make_action(caller_id=caller_id, owner_id=owner_id)
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

        action = _make_action(caller_id=caller_id, owner_id=owner_id)
        with with_user(_non_admin(caller_id)):
            with pytest.raises(NotEnoughPermission):
                await validator.validate(action, trigger_meta)
