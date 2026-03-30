from dataclasses import dataclass
from typing import override

from ai.backend.common.types import ImageID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.services.image.actions.resource_limit_base import ImageResourceLimitAction


@dataclass
class ClearImageCustomResourceLimitAction(ImageResourceLimitAction):
    """
    Deprecated. Use ClearImageCustomResourceLimitByIdAction instead.
    """

    image_canonical: str
    architecture: str

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class ClearImageCustomResourceLimitActionResult(BaseActionResult):
    image_data: ImageData

    @override
    def entity_id(self) -> str | None:
        return str(self.image_data.id)


@dataclass
class ClearImageCustomResourceLimitByIdAction(ImageResourceLimitAction):
    image_id: ImageID

    @override
    def entity_id(self) -> str | None:
        return str(self.image_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class ClearImageCustomResourceLimitByIdActionResult(BaseActionResult):
    image_data: ImageData

    @override
    def entity_id(self) -> str | None:
        return str(self.image_data.id)
