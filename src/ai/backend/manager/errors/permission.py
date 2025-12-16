"""Permission and RBAC-related error definitions."""

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)

__all__ = (
    "InsufficientPermission",
    "RoleNotFound",
    "RoleAlreadyAssigned",
    "RoleNotAssigned",
)


class InsufficientPermission(BackendAIError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/insufficient-permission"
    error_title = "Insufficient permission to perform this operation."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ROLE,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class RoleNotFound(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/role-not-found"
    error_title = "The role does not exist."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ROLE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class RoleAlreadyAssigned(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/role-already-assigned"
    error_title = "The role is already assigned to the user."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ROLE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )


class RoleNotAssigned(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/role-not-assigned"
    error_title = "The role is not assigned to the user."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ROLE,
            operation=ErrorOperation.HARD_DELETE,
            error_detail=ErrorDetail.NOT_FOUND,
        )
