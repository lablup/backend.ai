from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.models.vfs_storage import VFSStorageRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.vfs_storage.actions.base import VFSStorageAction


@dataclass
class UpdateVFSStorageAction(VFSStorageAction):
    updater: Updater[VFSStorageRow]

    @override
    def entity_id(self) -> str | None:
        return str(self.updater.pk_value)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "update"


@dataclass
class UpdateVFSStorageActionResult(BaseActionResult):
    result: VFSStorageData

    @override
    def entity_id(self) -> str | None:
        return str(self.result.id)
