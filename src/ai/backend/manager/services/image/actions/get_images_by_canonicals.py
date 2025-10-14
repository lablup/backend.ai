from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.image.types import (
    ImageStatus,
    ImageWithAgentStatus,
)
from ai.backend.manager.data.user.types import UserRole
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class GetImagesByCanonicalsAction(ImageAction):
    image_canonicals: list[str]
    user_role: UserRole
    image_status: Optional[list[ImageStatus]]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_by_canonicals"


@dataclass
class GetImagesByCanonicalsActionResult(BaseActionResult):
    images_with_agent_status: list[ImageWithAgentStatus]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.images_with_agent_status[0].image.id)
