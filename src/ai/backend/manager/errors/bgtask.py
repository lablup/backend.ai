"""
Background task-related exceptions.
"""

from __future__ import annotations

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class InvalidBgtaskId(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-bgtask-id"
    error_title = "Invalid background task ID format."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BGTASK,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )
