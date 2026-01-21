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
    @classmethod
    def operation_type(cls) -> str:
        return "scan"


@dataclass
class ScanImageActionResult(BaseActionResult):
    image: ImageData
    errors: list[str]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image.id)
