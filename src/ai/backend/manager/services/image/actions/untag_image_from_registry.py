import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class UntagImageFromRegistryAction(ImageAction):
    image_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.image_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "untag_from_registry"


@dataclass
class UntagImageFromRegistryActionResult(BaseActionResult):
    image: ImageData

    @override
    def entity_id(self) -> str | None:
        return str(self.image.id)
