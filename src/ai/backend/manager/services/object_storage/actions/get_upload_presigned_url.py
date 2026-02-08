import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.object_storage.actions.base import ObjectStorageAction


@dataclass
class GetUploadPresignedURLAction(ObjectStorageAction):
    artifact_revision_id: uuid.UUID
    key: str

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetUploadPresignedURLActionResult(BaseActionResult):
    storage_id: uuid.UUID
    presigned_url: str
    fields: dict[str, str]

    @override
    def entity_id(self) -> str | None:
        return str(self.storage_id)
