from typing import override

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.errors.common import ObjectNotFound


class EntityShareNotFound(ObjectNotFound):
    object_name = "entity-share"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ENTITY_SHARE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class DuplicateEntityShareError(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/duplicate-entity-share"
    error_title = "Duplicate entity invitation."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ENTITY_SHARE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class EntityShareInvalidStatus(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/entity-share-invalid-status"
    error_title = "Invalid entity invitation status transition."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ENTITY_SHARE,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.CONFLICT,
        )
