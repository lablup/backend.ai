from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.models.object_storage import ObjectStorageRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.object_storage.actions.base import ObjectStorageAction


@dataclass
class UpdateObjectStorageAction(ObjectStorageAction):
    updater: Updater[ObjectStorageRow]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.updater.pk_value)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "update"


@dataclass
class UpdateObjectStorageActionResult(BaseActionResult):
    result: ObjectStorageData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.result.id)
