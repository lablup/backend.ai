import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.vfs_storage.actions.base import VFSStorageAction


@dataclass
class DeleteVFSStorageAction(VFSStorageAction):
    storage_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.storage_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "delete"


@dataclass
class DeleteVFSStorageActionResult(BaseActionResult):
    deleted_storage_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.deleted_storage_id)
