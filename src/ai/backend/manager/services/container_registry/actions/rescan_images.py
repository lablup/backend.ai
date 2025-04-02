from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.services.container_registry.base import ContainerRegistryAction


@dataclass
class RescanImagesAction(ContainerRegistryAction):
    registry: str
    project: str
    # TODO: Pass progress_reporter?

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
    # TODO: Add type
    registry_row: ContainerRegistryRow

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.registry_row.id)
