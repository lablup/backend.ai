import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.services.object_storage.actions.base import ObjectStorageAction


@dataclass
class GetObjectStorageAction(ObjectStorageAction):
    storage_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.storage_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get"


@dataclass
class GetObjectStorageActionResult(BaseActionResult):
    result: ObjectStorageData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.result.id)
