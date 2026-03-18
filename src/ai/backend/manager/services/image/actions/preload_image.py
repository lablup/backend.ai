from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.common.types import ImageID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class PreloadImageAction(ImageAction):
    image_ids: list[ImageID]
    agents: list[str]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.IMAGE_PRELOAD

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class PreloadImageActionResult(BaseActionResult):
    images: list[ImageData]

    @override
    def entity_id(self) -> str | None:
        return None
