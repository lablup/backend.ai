from dataclasses import dataclass
from typing import override

from ai.backend.common.types import ImageID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.repositories.image.updaters import ImageUpdaterSpec
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class UpdateImageByIdAction(ImageAction):
    image_id: ImageID
    updater_spec: ImageUpdaterSpec

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_image_by_id"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateImageByIdActionResult:
    image: ImageData
