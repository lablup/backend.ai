from collections.abc import Mapping
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.types import ImageID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.image.types import (
    ImageStatus,
    ImageWithAgentInstallStatus,
)
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class GetAllImagesAction(ImageAction):
    status_filter: Optional[list[ImageStatus]]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_all_images"


@dataclass
class GetAllImagesActionResult(BaseActionResult):
    data: Mapping[ImageID, ImageWithAgentInstallStatus]

    @override
    def entity_id(self) -> Optional[str]:
        return None
