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
class DealiasImageAction(ImageAction):
    alias: str

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "dealias"


@dataclass
class DealiasImageActionResult(BaseActionResult):
    image_id: UUID
    image_alias: ImageAliasData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image_id)


class DealiasImageActionNoSuchAliasError(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/image-alias-not-found"
    error_title = "Image alias not found."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE_ALIAS,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.NOT_FOUND,
        )
