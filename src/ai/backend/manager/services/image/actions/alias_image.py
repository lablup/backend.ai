from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.image import ImageAliasRow
from ai.backend.manager.services.image.base import ImageAction


@dataclass
class AliasImageAction(ImageAction):
    image_canonical: str
    architecture: str
    alias: str

    @override
    def entity_id(self) -> str:
        # TODO: ?
        return f"{self.alias}"

    @override
    def operation_type(self):
        return "alias_image"


@dataclass
class AliasImageActionResult(BaseActionResult):
    image_alias: ImageAliasRow

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def status(self) -> str:
        return "success"

    @override
    def description(self) -> Optional[str]:
        return "The image has been aliased."

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, AliasImageActionResult):
            return False
        # TODO: 여기선 id로 비교못할 듯.
        return self.image_alias.alias == other.image_alias.alias


class AliasImageActionNoSuchAliasError(Exception):
    pass


# TODO: Remove this.
class AliasImageActionValueError(Exception):
    pass
