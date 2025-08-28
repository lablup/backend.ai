import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.object_storage_meta.types import ObjectStorageNamespaceData
from ai.backend.manager.services.object_storage.actions.base import ObjectStorageAction


@dataclass
class GetObjectStorageBucketsAction(ObjectStorageAction):
    storage_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.storage_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_buckets"


@dataclass
class GetObjectStorageBucketsActionResult(BaseActionResult):
    result: list[ObjectStorageNamespaceData]

    @override
    def entity_id(self) -> Optional[str]:
        return None
