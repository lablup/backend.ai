import uuid
from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.image.base import ImageAction


@dataclass
class ForgetImageByIdAction(ImageAction):
    user_id: uuid.UUID
    client_role: UserRole
    image_id: uuid.UUID

    @override
    def entity_id(self) -> str:
        return str(self.image_id)

    @override
    def operation_type(self):
        return "forget_image_by_id"


@dataclass
class ForgetImageByIdActionResult(BaseActionResult):
    # TODO: 여기서 ImageRow 타입을 그대로 써도 되는지?
    image_row: ImageRow

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def status(self) -> str:
        return "success"

    @override
    def description(self) -> Optional[str]:
        return "The image has been forgotten."

    # TODO: eq 직접 정의보다 나은 방법?
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ForgetImageByIdActionResult):
            return False
        return self.image_row.id == other.image_row.id


class ForgetImageActionByIdGenericForbiddenError(Exception):
    pass


class ForgetImageActionByIdObjectNotFoundError(Exception):
    pass
