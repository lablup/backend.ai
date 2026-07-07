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
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass
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


@dataclass(frozen=True)
class _Delegation:
    """A caller enqueuing a session on behalf of another owner."""

    caller_id: UserID
    owner_id: UserID
    caller: UserData  # non-admin user context to run the validator under


@pytest.fixture
def delegation() -> _Delegation:
    caller_id = UserID(uuid.uuid4())
    return _Delegation(
        caller_id=caller_id,
        owner_id=UserID(uuid.uuid4()),
        caller=UserData(
            user_id=caller_id,
            is_authorized=True,
            is_admin=False,
            is_superadmin=False,
            role=UserRole.USER,
            domain_name="default",
        ),
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
    def test_rbac_scope_targets_owner_when_delegating(
        self,
        delegated: bool,
        delegation: _Delegation,
    ) -> None:
        action = _make_action(
            user_id=delegation.caller_id,
            owner_id=delegation.owner_id if delegated else None,
        )
        # Delegation must authorize against the owner, never the caller.
        expected_id = delegation.owner_id if delegated else delegation.caller_id

        assert action.scope_id() == str(expected_id)
        target = action.target_element()
        assert target.element_type == RBACElementType.USER
        assert target.element_id == str(expected_id)


class TestEnqueueSessionDelegationAuthorization:
    @pytest.mark.parametrize(
        "granted, expectation",
        [
            (True, nullcontext()),
            (False, pytest.raises(NotEnoughPermission)),
        ],
        ids=["granted_passes", "denied_raises"],
    )
    async def test_delegation_authorizes_against_owner_scope(
        self,
        granted: bool,
        expectation: AbstractContextManager[object],
        trigger_meta: BaseActionTriggerMeta,
        delegation: _Delegation,
    ) -> None:
        repository = AsyncMock(spec=PermissionControllerRepository)
        repository.check_permission_with_scope_chain.return_value = granted
        validator = ScopeActionRBACValidator(repository, MagicMock())

        action = _make_action(user_id=delegation.caller_id, owner_id=delegation.owner_id)
        with with_user(delegation.caller):
            with expectation:
                await validator.validate(action, trigger_meta)

        # Regardless of the verdict, the check must target the owner's USER scope.
        repository.check_permission_with_scope_chain.assert_awaited_once()
        checked: ScopeChainPermissionCheckInput = (
            repository.check_permission_with_scope_chain.await_args.args[0]
        )
        assert checked.key.user_id == delegation.caller_id
        assert checked.key.element_type == RBACElementType.USER
        assert checked.key.entity_id == str(delegation.owner_id)
