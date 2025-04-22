from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class RBACException(BackendAIError):
    """Base exception for all RBAC related errors."""

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class InvalidScope(RBACException, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-scope"
    error_title = "Invalid scope specified."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class ScopeTypeMismatch(RBACException, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/scope-type-mismatch"
    error_title = "Scope type mismatch."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class NotEnoughPermission(RBACException, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/not-enough-permission"
    error_title = "Not enough permission."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.FORBIDDEN,
        )
