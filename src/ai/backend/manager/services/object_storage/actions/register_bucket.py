import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.object_storage_namespace.creator import ObjectStorageNamespaceCreator
from ai.backend.manager.data.object_storage_namespace.types import ObjectStorageNamespaceData
from ai.backend.manager.services.object_storage.actions.base import ObjectStorageAction


@dataclass
class RegisterBucketAction(ObjectStorageAction):
    creator: ObjectStorageNamespaceCreator

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
    result: ObjectStorageNamespaceData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.storage_id)
