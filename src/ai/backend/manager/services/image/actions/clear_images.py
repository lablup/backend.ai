from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.image.base import ImageAction


@dataclass
class ClearImagesAction(ImageAction):
    registry: str

    @override
    def entity_id(self) -> str:
        # TODO: ?
        return f"{self.registry}"

    @override
    def operation_type(self):
        return "clear_images"


@dataclass
class ClearImagesActionResult(BaseActionResult):
    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def status(self) -> str:
        return "success"

    @override
    def description(self) -> Optional[str]:
        return "The registry's images have been cleared."

    # TODO: 여기선 뭘로 비교해야 하지??
    # def __eq__(self, other: Any) -> bool:
    #     if not isinstance(other, ClearImagesActionResult):
    #         return False
    # return self.image_alias.alias == other.image_alias.alias


# TODO: Remove this.
class ClearImagesActionValueError(Exception):
    pass
