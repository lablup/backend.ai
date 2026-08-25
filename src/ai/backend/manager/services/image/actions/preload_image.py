from dataclasses import dataclass
from typing import override

from ai.backend.common.types import ImageID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class PreloadImageAction(ImageAction):
    image_ids: list[ImageID]
    agents: list[str]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "preload_image"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class PreloadImageActionResult:
    images: list[ImageData]
