from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.object_storage.creator import ObjectStorageCreator
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.services.object_storage.actions.base import ObjectStorageAction


@dataclass
class CreateObjectStorageAction(ObjectStorageAction):
    creator: ObjectStorageCreator

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create"


@dataclass
class CreateObjectStorageActionResult(BaseActionResult):
    result: ObjectStorageData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.result.id)
