import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.vfs_storage.actions.base import VFSStorageAction


@dataclass
class DeleteVFSStorageAction(VFSStorageAction):
    storage_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.storage_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeleteVFSStorageActionResult(BaseActionResult):
    deleted_storage_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.deleted_storage_id)
