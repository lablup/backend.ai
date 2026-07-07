"""RBAC scope targeting for EnqueueSessionAction owner delegation.

When a session is enqueued on behalf of another user (``owner_id`` set), the
RBAC scope must target the *owner's* USER scope so the validator authorizes the
caller against the owner rather than against the caller's own scope (which would
always pass and leave delegation unguarded).
"""

from __future__ import annotations

import uuid

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.types import SessionTypes
from ai.backend.manager.services.session.actions.enqueue_session import (
    EnqueueSessionAction,
    ResourceSlotEntry,
    SessionResourceSpec,
    SessionSchedulingSpec,
)


def _make_action(
    *,
    user_id: uuid.UUID,
    owner_id: uuid.UUID | None,
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


class TestEnqueueSessionActionDelegationScope:
    def test_without_owner_targets_caller(self) -> None:
        caller_id = uuid.uuid4()
        action = _make_action(user_id=caller_id, owner_id=None)

        assert action.delegated_owner_id() is None
        assert action.scope_id() == str(caller_id)
        target = action.target_element()
        assert target.element_type == RBACElementType.USER
        assert target.element_id == str(caller_id)

    def test_with_owner_targets_owner_not_caller(self) -> None:
        caller_id = uuid.uuid4()
        owner_id = uuid.uuid4()
        action = _make_action(user_id=caller_id, owner_id=owner_id)

        # Delegation must authorize against the owner, never the caller.
        assert action.delegated_owner_id() == str(owner_id)
        assert action.scope_id() == str(owner_id)
        target = action.target_element()
        assert target.element_type == RBACElementType.USER
        assert target.element_id == str(owner_id)
        assert target.element_id != str(caller_id)
