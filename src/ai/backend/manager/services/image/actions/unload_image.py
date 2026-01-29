from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class UnloadImageAction(ImageAction):
    image_ids: list[UUID]
    agents: list[str]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "unload"


@dataclass
class UnloadImageActionResult(BaseActionResult):
    images: list[ImageData]

    @override
    def entity_id(self) -> Optional[str]:
        return None
