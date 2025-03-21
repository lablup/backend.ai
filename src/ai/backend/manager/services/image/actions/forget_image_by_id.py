import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.exceptions import BaseActionException
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.image.base import ImageAction
from ai.backend.manager.services.image.types import ImageData


@dataclass
class ForgetImageByIdAction(ImageAction):
    user_id: uuid.UUID
    client_role: UserRole
    image_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image_id)

    @override
    def operation_type(self):
        return "forget_image_by_id"


@dataclass
class ForgetImageByIdActionResult(BaseActionResult):
    image: ImageData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image.id)


class ForgetImageActionByIdGenericForbiddenError(BaseActionException):
    pass


class ForgetImageActionByIdObjectNotFoundError(BaseActionException):
    pass
