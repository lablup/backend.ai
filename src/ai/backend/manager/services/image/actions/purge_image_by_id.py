import uuid
from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.image.base import ImageAction


@dataclass
class PurgeImageByIdAction(ImageAction):
    user_id: uuid.UUID
    client_role: UserRole
    image_id: uuid.UUID

    @override
    def entity_id(self) -> str:
        return str(self.image_id)

    @override
    def operation_type(self):
        return "purge_by_id"


@dataclass
class PurgeImageByIdActionResult(BaseActionResult):
    image_row: ImageRow

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def status(self) -> str:
        return "success"

    @override
    def description(self) -> Optional[str]:
        return "The image has been purged."

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, PurgeImageByIdActionResult):
            return False
        return self.image_row.id == other.image_row.id


class PurgeImageActionByIdGenericForbiddenError(Exception):
    pass


class PurgeImageActionByIdObjectNotFoundError(Exception):
    pass
