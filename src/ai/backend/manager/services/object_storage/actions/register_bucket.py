import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.object_storage_meta.creator import ObjectStorageMetaCreator
from ai.backend.manager.data.object_storage_meta.types import ObjectStorageMetaData
from ai.backend.manager.services.object_storage.actions.base import ObjectStorageAction


@dataclass
class RegisterBucketAction(ObjectStorageAction):
    creator: ObjectStorageMetaCreator

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "register_bucket"


@dataclass
class RegisterBucketActionResult(BaseActionResult):
    storage_id: uuid.UUID
    result: ObjectStorageMetaData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.storage_id)
