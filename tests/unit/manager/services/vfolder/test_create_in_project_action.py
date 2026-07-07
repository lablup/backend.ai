"""RBAC scope targeting for CreateVFolderInProjectAction owner delegation.

Project-owned vfolder creation is authorized against the PROJECT scope. The
optional ``owner_id`` only swaps the creating user's identity in the service and
must NOT change the RBAC target (which stays the project).
"""

from __future__ import annotations

import uuid

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.common.types import VFolderUsageMode
from ai.backend.manager.models.vfolder import VFolderPermission
from ai.backend.manager.services.vfolder.actions.vfolder_in_project import (
    CreateVFolderInProjectAction,
)


def _make_action(*, owner_id: uuid.UUID | None) -> CreateVFolderInProjectAction:
    return CreateVFolderInProjectAction(
        project_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        domain_name="default",
        name="test-vfolder",
        host=None,
        usage_mode=VFolderUsageMode.GENERAL,
        permission=VFolderPermission.READ_WRITE,
        cloneable=False,
        owner_id=owner_id,
    )


class TestCreateVFolderInProjectActionScope:
    def test_target_is_project_without_owner(self) -> None:
        action = _make_action(owner_id=None)

        assert action.scope_type() == ScopeType.PROJECT
        assert action.scope_id() == str(action.project_id)
        target = action.target_element()
        assert target.element_type == RBACElementType.PROJECT
        assert target.element_id == str(action.project_id)

    def test_target_stays_project_with_owner(self) -> None:
        action = _make_action(owner_id=uuid.uuid4())

        # Delegation must not move the RBAC target off the project.
        assert action.scope_id() == str(action.project_id)
        target = action.target_element()
        assert target.element_type == RBACElementType.PROJECT
        assert target.element_id == str(action.project_id)
