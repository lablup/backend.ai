from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.types import ImageID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class GetImageInstalledAgentCountsAction(ImageAction):
    image_ids: list[ImageID]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_installed_agent_counts"


@dataclass
class GetImageInstalledAgentCountsActionResult(BaseActionResult):
    data: dict[ImageID, int]

    @override
    def entity_id(self) -> Optional[str]:
        return None
