from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.services.image.actions.base import ImageSingleEntityAction


@dataclass
class RestoreImageByIdAction(ImageSingleEntityAction):
    """Put one forgotten image back in service."""

    @override
    @classmethod
    def action_name(cls) -> str:
        return "restore_image_by_id"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.RESTORE


@dataclass
class RestoreImageByIdActionResult:
    image: ImageData
