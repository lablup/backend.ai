from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.image.types import ImageAliasData
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class AliasImageByIdAction(ImageAction):
    image_id: UUID
    alias: str

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "alias_by_id"


@dataclass
class AliasImageByIdActionResult(BaseActionResult):
    image_id: UUID
    image_alias: ImageAliasData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image_id)
