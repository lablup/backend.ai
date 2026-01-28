import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class ForgetImageAction(ImageAction):
    """
    Deprecated. Use ForgetImageByIdAction instead.
    """

    user_id: uuid.UUID
    client_role: UserRole
    reference: str
    architecture: str

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "forget"


@dataclass
class ForgetImageActionResult(BaseActionResult):
    image: ImageData

    @override
    def entity_id(self) -> str | None:
        return str(self.image.id)


@dataclass
class ForgetImageByIdAction(ImageAction):
    user_id: uuid.UUID
    client_role: UserRole
    image_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "forget_by_id"


@dataclass
class ForgetImageByIdActionResult(BaseActionResult):
    image: ImageData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image.id)
