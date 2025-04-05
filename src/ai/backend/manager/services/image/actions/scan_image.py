from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class ScanImageAction(ImageAction):
    canonical: str
    architecture: str

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "scan"


@dataclass
class ScanImageActionResult(BaseActionResult):
    image: ImageData
    errors: list[str]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image.id)
