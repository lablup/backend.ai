import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.object_storage import OBJECT_STORAGE_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction


@dataclass
class GetUploadPresignedURLAction(BaseGlobalAction):
    artifact_revision_id: uuid.UUID
    key: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return OBJECT_STORAGE_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_upload_presigned_url"

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
