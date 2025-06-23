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
class PurgeImageByIdAction(ImageAction):
    user_id: uuid.UUID
    client_role: UserRole
    image_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "purge_by_id"


@dataclass
class PurgeImageByIdActionResult(BaseActionResult):
    image: ImageData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image.id)


class PurgeImageActionByIdGenericForbiddenError(BackendAIError):
    error_type = "https://api.backend.ai/probs/generic-forbidden"
    error_title = "Access to this resource is forbidden."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE,
            operation=ErrorOperation.HARD_DELETE,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class PurgeImageActionByIdObjectNotFoundError(BackendAIError):
    error_type = "https://api.backend.ai/probs/image-not-found"
    error_title = "Image not found."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE,
            operation=ErrorOperation.HARD_DELETE,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class PurgeImageActionByIdObjectDBError(BackendAIError):
    """
    This can occur when the alias of the image you are trying to delete already exists.
    """

    error_type = "https://api.backend.ai/probs/image-db-error"
    error_title = "Database error while purging image."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE,
            operation=ErrorOperation.HARD_DELETE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
