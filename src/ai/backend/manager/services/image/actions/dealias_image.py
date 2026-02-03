from dataclasses import dataclass
from typing import override

from ai.backend.common.types import ImageID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.image.types import ImageAliasData
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class DealiasImageAction(ImageAction):
    alias: str

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "dealias"


@dataclass
class DealiasImageActionResult(BaseActionResult):
    image_id: ImageID
    image_alias: ImageAliasData

    @override
    def entity_id(self) -> str | None:
        return str(self.image_id)
