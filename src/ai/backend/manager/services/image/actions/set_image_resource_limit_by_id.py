from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class SetImageResourceLimitByIdAction(ImageAction):
    image_id: UUID
    slot_name: str
    min_value: Optional[Decimal]
    max_value: Optional[Decimal]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "set_image_resource_limit_by_id"


@dataclass
class SetImageResourceLimitByIdActionResult(BaseActionResult):
    image_data: ImageData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image_data.id)
