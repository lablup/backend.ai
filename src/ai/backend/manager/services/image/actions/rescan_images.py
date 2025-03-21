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
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "rescan_images"


# TODO: BatchAction으로 업데이트, entity_ids는 image row ids로.
@dataclass
class RescanImagesActionResult(BaseActionResult):
    # TODO: DispatchResult 제거하고 list[ImageRow]는 별도의 dataclass로 변경
    result: DispatchResult[list[ImageRow]]

    @override
    def entity_id(self) -> Optional[str]:
        return None
