import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.image.actions.base import ImageAction


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
    @classmethod
    def operation_type(cls) -> str:
        return "forget"


@dataclass
class ForgetImageActionResult(BaseActionResult):
    image: ImageData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image.id)


class ForgetImageActionGenericForbiddenError(BackendAIError):
    error_type = "https://api.backend.ai/probs/generic-forbidden"
    error_title = "Access to this resource is forbidden."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE,
            operation=ErrorOperation.SOFT_DELETE,
            error_detail=ErrorDetail.FORBIDDEN,
        )
