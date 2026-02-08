from dataclasses import dataclass
from typing import override

from ai.backend.common.types import ImageID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.image.types import ImageAliasData
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class AliasImageAction(ImageAction):
    """
    Deprecated. Use AliasImageByIdAction instead.
    """

    image_canonical: str
    architecture: str
    alias: str

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class AliasImageActionResult(BaseActionResult):
    image_id: ImageID
    image_alias: ImageAliasData

    @override
    def entity_id(self) -> str | None:
        return str(self.image_id)


@dataclass
class AliasImageByIdAction(ImageAction):
    image_id: ImageID
    alias: str

    @override
    def entity_id(self) -> str | None:
        return str(self.image_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class AliasImageByIdActionResult(BaseActionResult):
    image_id: ImageID
    image_alias: ImageAliasData

    @override
    def entity_id(self) -> str | None:
        return str(self.image_id)
