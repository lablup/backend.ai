import uuid
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.image.base import ImageAction


class ForgetImageByIdAction(ImageAction):
    client_role: UserRole
    image_id: uuid.UUID

    @override
    def entity_id(self) -> str:
        return str(self.image_id)

    @override
    def operation_type(self):
        return "forget_by_id"


class ForgetImageActionByIdResult(BaseActionResult):
    @override
    def entity_id(self) -> Optional[str]:
        return None
