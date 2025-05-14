from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.bgtask.bgtask import ProgressReporter
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.services.container_registry.actions.base import ContainerRegistryAction


@dataclass
class RescanImagesAction(ContainerRegistryAction):
    registry: str
    project: Optional[str]
    progress_reporter: Optional[ProgressReporter]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "rescan"


@dataclass
class RescanImagesActionResult(BaseActionResult):
    images: list[ImageData]
    registry: ContainerRegistryData
    errors: list[str]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.registry.id)
