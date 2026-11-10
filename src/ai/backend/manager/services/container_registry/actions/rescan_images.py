from dataclasses import dataclass
from typing import override

from ai.backend.common.bgtask.reporter import ProgressReporter
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.services.container_registry.actions.base import ContainerRegistryAction


@dataclass
class RescanImagesAction(ContainerRegistryAction):
    registry: str
    project: str | None
    progress_reporter: ProgressReporter | None

    @override
    @classmethod
    def action_name(cls) -> str:
        return "rescan_images"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class RescanImagesActionResult:
    images: list[ImageData]
    registry: ContainerRegistryData
    errors: list[str]
