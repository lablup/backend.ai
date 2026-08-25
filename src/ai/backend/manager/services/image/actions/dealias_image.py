from dataclasses import dataclass
from typing import override

from ai.backend.common.types import ImageID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.image.types import ImageAliasData
from ai.backend.manager.services.image.actions.alias_base import ImageAliasAction


@dataclass
class DealiasImageAction(ImageAliasAction):
    alias: str

    @override
    @classmethod
    def action_name(cls) -> str:
        return "dealias_image"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DealiasImageActionResult:
    image_id: ImageID
    image_alias: ImageAliasData
