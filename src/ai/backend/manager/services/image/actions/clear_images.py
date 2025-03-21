from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.exceptions import BaseActionException
from ai.backend.manager.services.image.base import ImageAction


# TODO: Batch로 변경?
@dataclass
class ClearImagesAction(ImageAction):
    registry: str

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "clear_images"


@dataclass
class ClearImagesActionResult(BaseActionResult):
    @override
    def entity_id(self) -> Optional[str]:
        return None


# TODO: Remove this.
class ClearImagesActionValueError(BaseActionException):
    pass
