from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.services.image.actions.base import ImageSingleEntityAction


@dataclass
class UntagImageFromRegistryAction(ImageSingleEntityAction):
    @override
    @classmethod
    def action_name(cls) -> str:
        return "untag_image_from_registry"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class UntagImageFromRegistryActionResult:
    image: ImageData
