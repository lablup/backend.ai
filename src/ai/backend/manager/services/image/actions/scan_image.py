from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class ScanImageAction(ImageAction):
    canonical: str
    architecture: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.IMAGE_SCAN

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class ScanImageActionResult(BaseActionResult):
    image: ImageData
    errors: list[str]

    @override
    def entity_id(self) -> str | None:
        return str(self.image.id)
