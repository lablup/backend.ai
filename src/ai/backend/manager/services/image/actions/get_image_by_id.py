from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.image.types import (
    ImageStatus,
    ImageWithAgentStatus,
)
from ai.backend.manager.data.user.types import UserRole
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class GetImageByIdAction(ImageAction):
    image_id: UUID
    user_role: UserRole
    image_status: Optional[list[ImageStatus]]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_by_id"


@dataclass
class GetImageByIdActionResult(BaseActionResult):
    image_with_agent_status: ImageWithAgentStatus

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image_with_agent_status.image.id)
