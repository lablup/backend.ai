from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.image.types import (
    ImageIdentifier,
    ImageStatus,
    ImageWithAgentInstallStatus,
)
from ai.backend.manager.data.user.types import UserRole
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class GetImageByIdentifierAction(ImageAction):
    image_identifier: ImageIdentifier
    user_role: UserRole
    image_status: Optional[list[ImageStatus]]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_by_identifier"


@dataclass
class GetImageByIdentifierActionResult(BaseActionResult):
    image_with_agent_install_status: ImageWithAgentInstallStatus

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image_with_agent_install_status.image.id)
