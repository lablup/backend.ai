from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
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
    def operation_type(cls) -> str:
        return "alias"


@dataclass
class AliasImageActionResult(BaseActionResult):
    image_id: UUID
    image_alias: ImageAliasData

    @override
    def entity_id(self) -> str | None:
        return str(self.image_id)


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
