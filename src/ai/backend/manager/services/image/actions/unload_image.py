from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class UnloadImageAction(ImageAction):
    image_id: UUID
    agents: list[str]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "unload"


@dataclass
class UnloadImageActionResult(BaseActionResult):
    image: ImageData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image.id)
