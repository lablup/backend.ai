from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class InvalidScope(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-scope"
    error_title = "Invalid scope specified."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.PERMISSION,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class ScopeTypeMismatch(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/scope-type-mismatch"
    error_title = "Scope type mismatch."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.PERMISSION,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.MISMATCH,
        )


class NotEnoughPermission(BackendAIError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/not-enough-permission"
    error_title = "Not enough permission."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.PERMISSION,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.FORBIDDEN,
        )
