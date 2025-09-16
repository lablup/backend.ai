import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.object_storage.actions.base import ObjectStorageAction


@dataclass
class GetUploadPresignedURLAction(ObjectStorageAction):
    artifact_revision_id: uuid.UUID
    key: str

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_upload_presigned_url"


@dataclass
class GetUploadPresignedURLActionResult(BaseActionResult):
    storage_id: uuid.UUID
    presigned_url: str
    fields: dict[str, str]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.storage_id)
