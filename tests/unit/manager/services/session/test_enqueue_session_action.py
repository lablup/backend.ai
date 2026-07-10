"""RBAC scope targeting and authorization for EnqueueSessionAction owner delegation."""

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
class _EnqueueOnBehalf:
    """A caller enqueuing a session on behalf of another user (the owner)."""

    caller_id: UserID  # who sends the request
    owner_id: UserID  # who the session is created for
    caller_user: UserData  # the caller's non-admin auth context


@pytest.fixture
def enqueue_on_behalf() -> _EnqueueOnBehalf:
    caller_id = UserID(uuid.uuid4())
    return _EnqueueOnBehalf(
        caller_id=caller_id,
        owner_id=UserID(uuid.uuid4()),
        caller_user=UserData(
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


class TestEnqueueSessionOwnerDelegation:
    """Enqueuing on behalf of an owner authorizes against the owner's USER scope.

    The action must target the owner's scope, not the caller's own scope which
    would always pass and leave delegation unguarded; the validator must then
    authorize against that scope. The permission lookup itself is the
    repository's job, so the authorization test mocks it.
    """

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
        enqueue_on_behalf: _EnqueueOnBehalf,
    ) -> None:
        action = _make_action(
            user_id=enqueue_on_behalf.caller_id,
            owner_id=enqueue_on_behalf.owner_id if delegated else None,
        )
        # Delegation must authorize against the owner, never the caller.
        expected_id = enqueue_on_behalf.owner_id if delegated else enqueue_on_behalf.caller_id

        assert action.scope_id() == str(expected_id)
        target = action.target_element()
        assert target.element_type == RBACElementType.USER
        assert target.element_id == str(expected_id)

    @pytest.mark.parametrize(
        "permission_granted, expected_outcome",
        [
            (True, nullcontext()),
            (False, pytest.raises(NotEnoughPermission)),
        ],
        ids=["permission_granted_allows", "permission_denied_raises"],
    )
    async def test_delegation_authorizes_against_owner_scope(
        self,
        permission_granted: bool,
        expected_outcome: AbstractContextManager[object],
        trigger_meta: BaseActionTriggerMeta,
        enqueue_on_behalf: _EnqueueOnBehalf,
    ) -> None:
        repository = AsyncMock(spec=PermissionControllerRepository)
        repository.check_permission_with_scope_chain.return_value = permission_granted
        validator = ScopeActionRBACValidator(repository, MagicMock())

        action = _make_action(
            user_id=enqueue_on_behalf.caller_id,
            owner_id=enqueue_on_behalf.owner_id,
        )
        with with_user(enqueue_on_behalf.caller_user):
            with expected_outcome:
                await validator.validate(action, trigger_meta)

        # Regardless of the verdict, the check must target the owner's USER scope.
        repository.check_permission_with_scope_chain.assert_awaited_once()
        checked: ScopeChainPermissionCheckInput = (
            repository.check_permission_with_scope_chain.await_args.args[0]
        )
        assert checked.key.user_id == enqueue_on_behalf.caller_id
        assert checked.key.element_type == RBACElementType.USER
        assert checked.key.entity_id == str(enqueue_on_behalf.owner_id)
