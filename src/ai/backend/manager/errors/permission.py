"""Permission and RBAC-related error definitions."""

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)

__all__ = ("RoleNotFound",)


class RoleNotFound(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/role-not-found"
    error_title = "The role does not exist."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )
