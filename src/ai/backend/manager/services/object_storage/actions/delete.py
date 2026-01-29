import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.object_storage.actions.base import ObjectStorageAction


@dataclass
class DeleteObjectStorageAction(ObjectStorageAction):
    storage_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.storage_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "delete"


@dataclass
class DeleteObjectStorageActionResult(BaseActionResult):
    deleted_storage_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.deleted_storage_id)
