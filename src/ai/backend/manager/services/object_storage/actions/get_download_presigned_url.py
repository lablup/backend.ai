import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.object_storage.actions.base import ObjectStorageAction


@dataclass
class GetDownloadPresignedURLAction(ObjectStorageAction):
    artifact_id: uuid.UUID
    storage_id: uuid.UUID
    bucket_name: str
    key: str

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.storage_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_presigned_url"


@dataclass
class GetDownloadPresignedURLActionResult(BaseActionResult):
    storage_id: uuid.UUID
    presigned_url: str

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.storage_id)
