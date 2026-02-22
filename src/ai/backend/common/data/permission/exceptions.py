from __future__ import annotations

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class InvalidTypeConversionError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/permission-invalid-type-conversion"
    error_title = "Invalid Permission Type Conversion"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.PERMISSION,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.BAD_REQUEST,
        )
