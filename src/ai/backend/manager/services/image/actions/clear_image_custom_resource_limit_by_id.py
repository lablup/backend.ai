from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class ClearImageCustomResourceLimitByIdAction(ImageAction):
    image_id: UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "clear_image_custom_resource_limit_by_id"


@dataclass
class ClearImageCustomResourceLimitByIdActionResult(BaseActionResult):
    image_data: ImageData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image_data.id)
