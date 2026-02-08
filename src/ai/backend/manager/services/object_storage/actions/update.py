from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.models.object_storage import ObjectStorageRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.object_storage.actions.base import ObjectStorageAction


@dataclass
class UpdateObjectStorageAction(ObjectStorageAction):
    updater: Updater[ObjectStorageRow]

    @override
    def entity_id(self) -> str | None:
        return str(self.updater.pk_value)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateObjectStorageActionResult(BaseActionResult):
    result: ObjectStorageData

    @override
    def entity_id(self) -> str | None:
        return str(self.result.id)
