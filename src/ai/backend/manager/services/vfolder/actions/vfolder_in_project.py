"""Creation of a vfolder owned by a project."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE
from ai.backend.common.data.entity.types import ScopeRef
from ai.backend.common.types import VFolderUsageMode
from ai.backend.manager.actions.types import ActionOperationType
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

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=self.project_id),)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_vfolder_in_project"


@dataclass
class CreateVFolderInProjectActionResult(VFolderScopeActionResult):
    project_id: uuid.UUID
    vfolder: VFolderData
