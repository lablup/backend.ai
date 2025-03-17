import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
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
    def entity_id(self) -> str:
        return f"{self.reference} ({self.architecture})"

    @override
    def operation_type(self):
        return "forget"


@dataclass
class ForgetImageActionResult(BaseActionResult): ...


@dataclass
class ForgetImageActionSuccess(ForgetImageActionResult):
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


@dataclass
class ForgetImageActionGenericForbiddenError(ForgetImageActionResult):
    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def status(self) -> str:
        return "forbidden error"

    @override
    def description(self) -> Optional[str]:
        return "The user role is not allowed to forget the image."
