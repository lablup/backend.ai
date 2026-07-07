"""RBAC-enforced v2 VFolder actions.

Create is PROJECT-scoped (entity doesn't exist yet) and uses
``ScopeActionProcessor`` with ``scope_rbac_validators``.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.common.identifier.user import UserID
from ai.backend.common.types import VFolderUsageMode
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.models.vfolder import VFolderPermission
from ai.backend.manager.services.vfolder.actions.base import (
    VFolderScopeAction,
    VFolderScopeActionResult,
)

# ---------------------------------------------------------------------------
# Create (scope action — entity does not exist yet, requires project_id)
# ---------------------------------------------------------------------------


@dataclass
class CreateVFolderInProjectAction(VFolderScopeAction):
    """Create a vfolder owned by a specific project."""

    project_id: uuid.UUID
    user_id: uuid.UUID
    domain_name: str
    name: str
    host: str | None
    usage_mode: VFolderUsageMode
    permission: VFolderPermission
    cloneable: bool
    owner_id: UserID | None = None
    """Delegated owner user UUID. When set, the service records the vfolder as
    created by that user instead of the caller. Authorization stays
    PROJECT-scoped (the caller needs CREATE on the project)."""

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.PROJECT

    @override
    def scope_id(self) -> str:
        return str(self.project_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.PROJECT,
            element_id=str(self.project_id),
        )


@dataclass
class CreateVFolderInProjectActionResult(VFolderScopeActionResult):
    project_id: uuid.UUID
    vfolder: VFolderData

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder.id)

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.PROJECT

    @override
    def scope_id(self) -> str:
        return str(self.project_id)
