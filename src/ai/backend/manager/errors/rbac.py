from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)

from .common import ObjectNotFound


class RoleNotFound(ObjectNotFound, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/role-not-found"
    error_title = "The specified role was not found."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.PERMISSION,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class UserSystemRoleNotFound(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/user-system-role-not-found"
    error_title = "The user does not have a system role assigned."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.PERMISSION,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )
