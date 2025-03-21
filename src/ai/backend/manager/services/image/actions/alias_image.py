from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.exceptions import BaseActionException
from ai.backend.manager.models.image import ImageAliasRow
from ai.backend.manager.services.image.base import ImageAction


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
        return "alias_image"


@dataclass
class AliasImageActionResult(BaseActionResult):
    image_alias: ImageAliasRow

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image_alias.image_id)


class AliasImageActionNoSuchAliasError(BaseActionException):
    pass


# TODO: Remove this.
class AliasImageActionValueError(BaseActionException):
    pass
