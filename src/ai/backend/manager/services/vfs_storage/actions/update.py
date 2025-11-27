import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.vfs_storage.modifier import VFSStorageModifier
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.services.vfs_storage.actions.base import VFSStorageAction


@dataclass
class UpdateVFSStorageAction(VFSStorageAction):
    id: uuid.UUID
    modifier: VFSStorageModifier

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "update"


@dataclass
class UpdateVFSStorageActionResult(BaseActionResult):
    result: VFSStorageData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.result.id)
