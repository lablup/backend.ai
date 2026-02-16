from __future__ import annotations

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class InvalidTypeConversion(BackendAIError, web.HTTPInternalServerError):
    """Raised when converting between EntityType and ScopeType fails."""

    error_type = "https://api.backend.ai/probs/invalid-type-conversion"
    error_title = "Invalid Type Conversion"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.RBAC,
            operation=ErrorOperation.PARSING,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
