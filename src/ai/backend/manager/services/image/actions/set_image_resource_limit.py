from dataclasses import dataclass
from typing import override

from ai.backend.common.types import ImageID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.image.types import ImageData, ResourceLimitInput
from ai.backend.manager.services.image.actions.resource_limit_base import ImageResourceLimitAction


@dataclass
class SetImageResourceLimitByIdAction(ImageResourceLimitAction):
    image_id: ImageID
    resource_limit: ResourceLimitInput

    @override
    def entity_id(self) -> str | None:
        return str(self.image_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class SetImageResourceLimitByIdActionResult(BaseActionResult):
    image_data: ImageData

    @override
    def entity_id(self) -> str | None:
        return str(self.image_data.id)
