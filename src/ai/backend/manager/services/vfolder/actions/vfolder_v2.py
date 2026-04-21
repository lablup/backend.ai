"""V2 vfolder action definitions."""

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import (
    EntityType,
    RBACElementType,
    ScopeType,
)
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.action.scope import BaseScopeAction
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.vfolder.actions.base import (
    VFolderSingleEntityAction,
    VFolderSingleEntityActionResult,
)


@dataclass
class DeleteVFolderV2Action(VFolderSingleEntityAction):
    """Soft-delete a vfolder by ID with RBAC enforcement."""

    vfolder_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    def target_entity_id(self) -> str:
        return str(self.vfolder_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.VFOLDER,
            element_id=str(self.vfolder_id),
        )


@dataclass
class DeleteVFolderV2ActionResult(VFolderSingleEntityActionResult):
    vfolder_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_id)

    @override
    def target_entity_id(self) -> str:
        return str(self.vfolder_id)


@dataclass
class PurgeVFolderV2Action(BaseScopeAction):
    user_id: uuid.UUID
    vfolder_id: uuid.UUID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.VFOLDER

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_id)

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return str(self.user_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.VFOLDER,
            element_id=str(self.vfolder_id),
        )


@dataclass
class PurgeVFolderV2ActionResult(BaseActionResult):
    vfolder_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_id)
