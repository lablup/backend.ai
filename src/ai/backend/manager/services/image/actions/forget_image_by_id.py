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
        return "forget_by_id"


@dataclass
class ForgetImageByIdActionResult(BaseActionResult): ...


@dataclass
class ForgetImageActionByIdSuccess(ForgetImageByIdActionResult):
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
        if not isinstance(other, ForgetImageActionByIdSuccess):
            return False
        return self.image_row.id == other.image_row.id


@dataclass
class ForgetImageActionByIdGenericForbiddenError(ForgetImageByIdActionResult):
    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def status(self) -> str:
        return "forbidden error"

    @override
    def description(self) -> Optional[str]:
        return "The user role is not allowed to forget the image."


@dataclass
class ForgetImageActionByIdObjectNotFoundError(ForgetImageByIdActionResult):
    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def status(self) -> str:
        return "object not found"

    @override
    def description(self) -> Optional[str]:
        return "The image does not exist."
