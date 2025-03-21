import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.exceptions import BaseActionException
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.image.base import ImageAction


@dataclass
class ForgetImageAction(ImageAction):
    user_id: uuid.UUID
    client_role: UserRole
    reference: str
    architecture: str

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "forget_image"


@dataclass
class ForgetImageActionResult(BaseActionResult):
    image_row: ImageRow

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image_row.id)


class ForgetImageActionGenericForbiddenError(BaseActionException):
    pass
