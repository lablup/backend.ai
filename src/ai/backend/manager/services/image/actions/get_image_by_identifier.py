from dataclasses import dataclass
from typing import override

from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.image.types import (
    ImageIdentifier,
    ImageStatus,
    ImageWithAgentInstallStatus,
)
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class GetImageByIdentifierAction(ImageAction):
    image_identifier: ImageIdentifier
    user_role: UserRole
    image_status: list[ImageStatus] | None

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_by_identifier"


@dataclass
class GetImageByIdentifierActionResult(BaseActionResult):
    image_with_agent_install_status: ImageWithAgentInstallStatus

    @override
    def entity_id(self) -> str | None:
        return str(self.image_with_agent_install_status.image.id)
