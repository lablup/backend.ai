"""Global entity error definitions."""

from typing import override

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)

__all__ = (
    "GlobalEntityMissing",
    "GlobalEntityNotLoaded",
)


class GlobalEntityNotLoaded(BackendAIError, web.HTTPInternalServerError):
    """Raised when a global entity id is read before the ids are loaded."""

    error_type = "https://api.backend.ai/probs/global-entity-not-loaded"
    error_title = "The global entity ids are not loaded."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.PERMISSION,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_READY,
        )


class GlobalEntityMissing(BackendAIError, web.HTTPInternalServerError):
    """Raised when a global entity row or its virtual entity does not exist."""

    error_type = "https://api.backend.ai/probs/global-entity-missing"
    error_title = "A global entity or its virtual entity does not exist."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.PERMISSION,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )
