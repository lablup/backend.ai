import uuid
from dataclasses import dataclass
from typing import Any, Optional, override

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
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "forget_image"


@dataclass
class ForgetImageActionResult(BaseActionResult):
    # TODO: 여기서 ImageRow 타입을 그대로 써도 되는지?
    image_row: ImageRow

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image_row.id)

    @override
    def status(self) -> str:
        return "success"

    @override
    def description(self) -> str:
        return "The image has been forgotten."

    # TODO: eq 직접 정의보다 나은 방법?
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ForgetImageActionResult):
            return False
        return self.image_row.id == other.image_row.id


# TODO: BackendError를 상속해야함?
# BackendError를 상속하면 생성자 호출될 때 에러남.
class ForgetImageActionGenericForbiddenError(Exception):
    pass
