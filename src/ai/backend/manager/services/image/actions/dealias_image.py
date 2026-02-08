from dataclasses import dataclass
from typing import override

from ai.backend.common.types import ImageID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.image.types import ImageAliasData
from ai.backend.manager.services.image.actions.alias_base import ImageAliasAction


@dataclass
class DealiasImageAction(ImageAliasAction):
    alias: str

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DealiasImageActionResult(BaseActionResult):
    image_id: ImageID
    image_alias: ImageAliasData

    @override
    def entity_id(self) -> str | None:
        return str(self.image_id)
