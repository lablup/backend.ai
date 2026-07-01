import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import (
    EntityType,
    RBACElementType,
    ScopeType,
)
from ai.backend.common.types import VFolderUsageMode
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.action.scope import BaseScopeAction
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.models.vfolder import VFolderPermission


@dataclass
class CreateVFolderV2Action(BaseScopeAction):
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
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.VFOLDER

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.PROJECT if self.project_id else ScopeType.USER

    @override
    def scope_id(self) -> str:
        return str(self.project_id) if self.project_id else str(self.user_id)

    @override
    def target_element(self) -> RBACElementRef:
        if self.project_id:
            return RBACElementRef(
                element_type=RBACElementType.PROJECT,
                element_id=str(self.project_id),
            )
        return RBACElementRef(
            element_type=RBACElementType.USER,
            element_id=str(self.user_id),
        )


@dataclass
class CreateVFolderV2ActionResult(BaseActionResult):
    vfolder: VFolderData

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder.id)
