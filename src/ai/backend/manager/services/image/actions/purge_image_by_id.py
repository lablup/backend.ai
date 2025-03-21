import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.exceptions import BaseActionException
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.image.base import ImageAction


@dataclass
class PurgeImageByIdAction(ImageAction):
    user_id: uuid.UUID
    client_role: UserRole
    image_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image_id)

    @override
    def operation_type(self):
        return "purge_image_by_id"


@dataclass
class PurgeImageByIdActionResult(BaseActionResult):
    image_row: ImageRow

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image_row.id)


class PurgeImageActionByIdGenericForbiddenError(BaseActionException):
    pass


class PurgeImageActionByIdObjectNotFoundError(BaseActionException):
    pass
