from collections.abc import Mapping
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.types import AgentId, ImageID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class GetImageInstalledAgentsAction(ImageAction):
    image_ids: list[ImageID]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_installed_agents"


@dataclass
class GetImageInstalledAgentsActionResult(BaseActionResult):
    data: Mapping[ImageID, set[AgentId]]

    @override
    def entity_id(self) -> Optional[str]:
        return None
