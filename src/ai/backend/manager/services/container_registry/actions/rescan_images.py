from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.services.container_registry.base import ContainerRegistryAction


@dataclass
class RescanImagesAction(ContainerRegistryAction):
    registry: str
    project: str

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "rescan"


@dataclass
class RescanImagesActionResult(BaseActionResult):
    images: list[ImageData]
    errors: list[str]

    @override
    def entity_id(self) -> Optional[str]:
        return None
