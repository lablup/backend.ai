from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.exceptions import BaseActionException
from ai.backend.manager.data.image.types import ImageAliasData
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class AliasImageAction(ImageAction):
    image_canonical: str
    architecture: str
    alias: str

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "alias"


@dataclass
class AliasImageActionResult(BaseActionResult):
    image_id: UUID
    image_alias: ImageAliasData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image_id)

    # TODO: Find a way to compare image alias row ID
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AliasImageActionResult):
            return False
        return self.image_alias.alias == other.image_alias.alias


class AliasImageActionNoSuchAliasError(BaseActionException):
    pass


# TODO: Is this required?
class AliasImageActionValueError(BaseActionException):
    pass


class AliasImageActionDBError(BaseActionException):
    """
    This can occur when an image alias with the same value already exists.
    """

    pass
