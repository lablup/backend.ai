from dataclasses import dataclass
from typing import override

from ai.backend.common.types import ImageID
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
    @classmethod
    def action_name(cls) -> str:
        return "clear_image_custom_resource_limit"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class ClearImageCustomResourceLimitActionResult:
    image_data: ImageData


@dataclass
class ClearImageCustomResourceLimitByIdAction(ImageResourceLimitAction):
    image_id: ImageID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "clear_image_custom_resource_limit_by_id"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class ClearImageCustomResourceLimitByIdActionResult:
    image_data: ImageData
