import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.session.types import CustomizedImageVisibilityScope
from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.session.base import SessionAction


@dataclass
class ConvertSessionToImageAction(SessionAction):
    session_name: str
    owner_access_key: AccessKey
    image_name: str
    image_visibility: CustomizedImageVisibilityScope
    image_owner_id: uuid.UUID
    user_email: str
    max_customized_image_count: int

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class ConvertSessionToImageActionResult(BaseActionResult):
    task_id: uuid.UUID

    session_data: SessionData

    @override
    def entity_id(self) -> str | None:
        return str(self.session_data.id)
