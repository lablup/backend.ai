from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.image import ImageAliasRow
from ai.backend.manager.services.image.base import ImageAction


@dataclass
class DealiasImageAction(ImageAction):
    alias: str

    @override
    def entity_id(self) -> str:
        # TODO: ?
        return f"{self.alias}"

    @override
    def operation_type(self):
        return "dealias_image"


@dataclass
class DealiasImageActionResult(BaseActionResult):
    image_alias: ImageAliasRow

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def status(self) -> str:
        return "success"

    @override
    def description(self) -> Optional[str]:
        return "The image has been dealiased."

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, DealiasImageActionResult):
            return False
        return self.image_alias.id == other.image_alias.id


class DealiasImageActionNoSuchAliasError(Exception):
    pass


# TODO: Remove this.
class DealiasImageActionValueError(Exception):
    pass
