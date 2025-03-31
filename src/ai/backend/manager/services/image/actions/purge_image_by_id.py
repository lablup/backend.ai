import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.exceptions import BaseActionException
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.image.actions.base import ImageAction


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
        return "purge_by_id"


@dataclass
class PurgeImageByIdActionResult(BaseActionResult):
    image: ImageData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image.id)


class PurgeImageActionByIdGenericForbiddenError(BaseActionException):
    pass


class PurgeImageActionByIdObjectNotFoundError(BaseActionException):
    pass


class PurgeImageActionByIdObjectDBError(BaseActionException):
    """
    This can occur when the alias of the image you are trying to delete already exists.
    """

    pass
