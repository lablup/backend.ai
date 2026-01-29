import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.services.vfs_storage.actions.base import VFSStorageAction


@dataclass
class GetVFSStorageAction(VFSStorageAction):
    storage_id: uuid.UUID | None = None
    storage_name: str | None = None

    @override
    def entity_id(self) -> str | None:
        return str(self.storage_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get"


@dataclass
class GetVFSStorageActionResult(BaseActionResult):
    result: VFSStorageData

    @override
    def entity_id(self) -> str | None:
        return str(self.result.id)
