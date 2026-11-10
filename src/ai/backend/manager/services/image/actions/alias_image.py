from dataclasses import dataclass
from typing import override

from ai.backend.common.types import ImageID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.image.types import ImageAliasData
from ai.backend.manager.services.image.actions.alias_base import ImageAliasAction


@dataclass
class AliasImageAction(ImageAliasAction):
    """
    Deprecated. Use AliasImageByIdAction instead.
    """

    image_canonical: str
    architecture: str
    alias: str

    @override
    @classmethod
    def action_name(cls) -> str:
        return "alias_image"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class AliasImageActionResult:
    image_id: ImageID
    image_alias: ImageAliasData


@dataclass
class AliasImageByIdAction(ImageAliasAction):
    image_id: ImageID
    alias: str

    @override
    @classmethod
    def action_name(cls) -> str:
        return "alias_image_by_id"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class AliasImageByIdActionResult:
    image_id: ImageID
    image_alias: ImageAliasData
