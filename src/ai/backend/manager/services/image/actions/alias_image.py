from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.image.types import ImageAliasData
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class AliasImageAction(ImageAction):
    image_canonical: str
    architecture: str
    alias: str

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "alias"


@dataclass
class AliasImageActionResult(BaseActionResult):
    image_id: UUID
    image_alias: ImageAliasData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image_id)


class AliasImageActionValueError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-parameters"
    error_title = "Invalid parameters for image alias."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE_ALIAS,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class AliasImageActionDBError(BackendAIError, web.HTTPInternalServerError):
    """
    This can occur when an image alias with the same value already exists.
    """

    error_type = "https://api.backend.ai/probs/image-db-error"
    error_title = "Database error while managing image alias."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE_ALIAS,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )
