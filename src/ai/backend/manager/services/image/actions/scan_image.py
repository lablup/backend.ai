from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.image import ImageEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class ScanImageAction(ImageAction):
    canonical: str
    architecture: str

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scan_image"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class ScanImageActionResult:
    image: ImageData
    errors: list[str]


@dataclass(frozen=True)
class GlobalScanImageAction(BaseGlobalAction):
    canonical: str
    architecture: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ImageEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_scan_image"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass(frozen=True)
class GlobalScanImageActionResult:
    image: ImageData
