from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.image import ImageEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.data.image.types import ImageData


@dataclass(frozen=True)
class GlobalRescanImageAction(BaseGlobalAction):
    canonical: str
    architecture: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ImageEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_rescan_image"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass(frozen=True)
class GlobalRescanImageActionResult:
    image: ImageData
