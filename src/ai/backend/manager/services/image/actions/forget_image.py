from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.services.image.actions.base import (
    ImageAction,
    ImageSingleEntityAction,
)


@dataclass
class ForgetImageAction(ImageAction):
    """
    Deprecated. Use ForgetImageByIdAction instead.
    """

    reference: str
    architecture: str

    @override
    @classmethod
    def action_name(cls) -> str:
        return "forget_image"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class ForgetImageActionResult:
    image: ImageData


@dataclass
class ForgetImageByIdAction(ImageSingleEntityAction):
    @override
    @classmethod
    def action_name(cls) -> str:
        return "forget_image_by_id"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class ForgetImageByIdActionResult:
    image: ImageData
