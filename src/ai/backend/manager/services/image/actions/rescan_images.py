from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.image.types import RescanImagesResult
from ai.backend.manager.services.image.base import ImageAction


# TODO: Change this to Batch Action
@dataclass
class RescanImagesAction(ImageAction):
    registry: Optional[str] = None
    project: Optional[str] = None

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "rescan_multi"


@dataclass
class RescanImagesActionResult(BaseActionResult):
    rescan_result: RescanImagesResult

    @override
    def entity_id(self) -> Optional[str]:
        return None
