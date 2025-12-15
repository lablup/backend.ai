from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.models.vfs_storage import VFSStorageRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.services.vfs_storage.actions.base import VFSStorageAction


@dataclass
class CreateVFSStorageAction(VFSStorageAction):
    creator: Creator[VFSStorageRow]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create"


@dataclass
class CreateVFSStorageActionResult(BaseActionResult):
    result: VFSStorageData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.result.id)
