"""Permission and RBAC-related error definitions."""

from typing import override

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)

__all__ = ("NotEnoughPermission",)


class NotEnoughPermission(BackendAIError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/not-enough-permission"
    error_title = "Insufficient permission to perform this operation."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.PERMISSION,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.FORBIDDEN,
        )
