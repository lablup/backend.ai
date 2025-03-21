from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.image.base import ImageAction


@dataclass
class PreloadImageAction(ImageAction):
    references: list[str]
    agents: list[str]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "preload_image"


@dataclass
class PreloadImageActionResult(BaseActionResult):
    @override
    def entity_id(self) -> Optional[str]:
        return None
