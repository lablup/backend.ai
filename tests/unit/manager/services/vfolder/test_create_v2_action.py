"""RBAC scope targeting for CreateVFolderV2Action owner delegation.

When a vfolder is created on behalf of another user (``owner_id`` set), the
RBAC scope must target the *owner's* USER scope so the validator authorizes the
caller against the owner rather than the caller's own scope. Project-scoped
creation is unaffected (authorization stays PROJECT-scoped).
"""

from __future__ import annotations

import uuid

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.types import VFolderUsageMode
from ai.backend.manager.models.vfolder import VFolderPermission
from ai.backend.manager.services.vfolder.actions.create_v2 import CreateVFolderV2Action


def _make_action(
    *,
    user_id: uuid.UUID,
    owner_id: uuid.UUID | None,
    project_id: uuid.UUID | None = None,
) -> CreateVFolderV2Action:
    return CreateVFolderV2Action(
        name="test-vfolder",
        user_id=user_id,
        domain_name="default",
        project_id=project_id,
        host=None,
        usage_mode=VFolderUsageMode.GENERAL,
        permission=VFolderPermission.READ_WRITE,
        cloneable=False,
        owner_id=owner_id,
    )


class TestCreateVFolderV2ActionDelegationScope:
    def test_without_owner_targets_caller(self) -> None:
        caller_id = uuid.uuid4()
        action = _make_action(user_id=caller_id, owner_id=None)

        assert action.scope_id() == str(caller_id)
        target = action.target_element()
        assert target.element_type == RBACElementType.USER
        assert target.element_id == str(caller_id)

    def test_with_owner_targets_owner_not_caller(self) -> None:
        caller_id = uuid.uuid4()
        owner_id = uuid.uuid4()
        action = _make_action(user_id=caller_id, owner_id=owner_id)

        # Delegation must authorize against the owner, never the caller.
        assert action.scope_id() == str(owner_id)
        target = action.target_element()
        assert target.element_type == RBACElementType.USER
        assert target.element_id == str(owner_id)
        assert target.element_id != str(caller_id)

    def test_project_scope_ignores_owner(self) -> None:
        project_id = uuid.uuid4()
        action = _make_action(
            user_id=uuid.uuid4(), owner_id=uuid.uuid4(), project_id=project_id
        )

        # Project-owned vfolders authorize against the project, not a user.
        assert action.scope_id() == str(project_id)
        target = action.target_element()
        assert target.element_type == RBACElementType.PROJECT
        assert target.element_id == str(project_id)
