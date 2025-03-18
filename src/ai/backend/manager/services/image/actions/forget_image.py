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
    def entity_id(self) -> str:
        return f"{self.reference} ({self.architecture})"

    @override
    def operation_type(self):
        return "forget"


@dataclass
class ForgetImageActionResult(BaseActionResult):
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
        if not isinstance(other, ForgetImageActionResult):
            return False
        return self.image_row.id == other.image_row.id


class ForgetImageActionGenericForbiddenError(Exception):
    """
    Indicates that forgetting an image action is forbidden by policy or configuration.
    """

    pass
    # error_type: str = "https://api.backend.ai/probs/forget-image-action-generic-forbidden"
    # error_title: str = "Forbidden to forget image"

    # def __init__(
    #     self,
    #     extra_msg: Optional[str] = None,
    #     extra_data: Optional[Any] = None,
    #     **kwargs
    # ):
    #     kwargs.setdefault("status", 403)
    #     kwargs.setdefault("reason", "Forbidden")

    #     super().__init__(extra_msg=extra_msg, extra_data=extra_data, **kwargs)
