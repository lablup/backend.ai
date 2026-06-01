"""V2 vfolder action definitions."""

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
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
class PurgeVFolderV2Action(VFolderSingleEntityAction):
    """Permanently purge a vfolder by ID with RBAC enforcement.

    By default the call is rejected when any model card references the
    vfolder. Set ``cascade_model_card=True`` to also remove the linked
    model card row(s) atomically.
    """

    vfolder_id: uuid.UUID
    cascade_model_card: bool = False

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

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
class PurgeVFolderV2ActionResult(VFolderSingleEntityActionResult):
    vfolder_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_id)

    @override
    def target_entity_id(self) -> str:
        return str(self.vfolder_id)
