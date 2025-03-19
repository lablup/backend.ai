from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.types import DispatchResult
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.services.image.base import ImageAction


@dataclass
class RescanImagesAction(ImageAction):
    registry: Optional[str] = None
    project: Optional[str] = None

    @override
    def entity_id(self) -> str:
        # TODO: ?
        return f"{self.registry}"

    @override
    def operation_type(self):
        return "rescan_images"


@dataclass
class RescanImagesActionResult(BaseActionResult):
    result: DispatchResult[list[ImageRow]]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def status(self) -> str:
        return "success"

    @override
    def description(self) -> Optional[str]:
        return self.result.message()

    @override
    def to_bgtask_result(self) -> DispatchResult:
        return self.result

    # TODO: 여기선 어떻게 비교?
    # def __eq__(self, other: Any) -> bool:
    #     if not isinstance(other, AliasImageActionResult):
    #         return False
    #     return self.image_alias.alias == other.image_alias.alias
