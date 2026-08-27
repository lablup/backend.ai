import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.project import PROJECT_ENTITY_TYPE, PROJECT_SCOPE_TYPE
from ai.backend.common.data.entity.types import EntityType, ScopeRef
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE, USER_SCOPE_TYPE
from ai.backend.common.types import VFolderUsageMode
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.models.vfolder import VFolderPermission
from ai.backend.manager.services.vfolder.actions.base import (
    VFolderScopeAction,
    VFolderScopeActionResult,
)


@dataclass
class CreateVFolderV2Action(VFolderScopeAction):
    """Create a new vfolder. Policy is resolved internally from user_id."""

    name: str
    user_id: uuid.UUID
    domain_name: str
    project_id: uuid.UUID | None
    host: str | None
    usage_mode: VFolderUsageMode
    permission: VFolderPermission
    cloneable: bool

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        """A folder without a project belongs to the user who creates it."""
        if self.project_id is not None:
            return (ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=self.project_id),)
        return (ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=self.user_id),)

    @override
    @classmethod
    def available_scope_types(cls) -> Sequence[EntityType]:
        return (PROJECT_ENTITY_TYPE, USER_ENTITY_TYPE)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_vfolder_v2"


@dataclass
class CreateVFolderV2ActionResult(VFolderScopeActionResult):
    vfolder: VFolderData
