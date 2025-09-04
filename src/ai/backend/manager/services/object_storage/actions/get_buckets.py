import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.object_storage_namespace.types import ObjectStorageNamespaceData
from ai.backend.manager.services.object_storage.actions.base import ObjectStorageAction


@dataclass
class GetBucketsAction(ObjectStorageAction):
    storage_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.storage_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_buckets"


@dataclass
class GetBucketsActionResult(BaseActionResult):
    result: list[ObjectStorageNamespaceData]

    @override
    def entity_id(self) -> Optional[str]:
        return None
