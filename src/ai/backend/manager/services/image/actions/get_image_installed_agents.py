from collections.abc import Mapping
from dataclasses import dataclass
from typing import override

from ai.backend.common.types import AgentId, ImageID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class GetImageInstalledAgentsAction(ImageAction):
    image_ids: list[ImageID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_image_installed_agents"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetImageInstalledAgentsActionResult:
    data: Mapping[ImageID, set[AgentId]]
