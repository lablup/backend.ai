"""HTTP-related errors for App Proxy."""

from __future__ import annotations

from typing import Any

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.common.plugin.hook import HookResult


class URLNotFound(BackendAIError):
    """Raised when URL path is not found."""

    error_type = "https://api.backend.ai/probs/url-not-found"
    error_title = "Unknown URL path."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ObjectNotFound(BackendAIError):
    """Raised when requested object is not found."""

    error_type = "https://api.backend.ai/probs/object-not-found"
    error_title = "E00002: No such object."

    def __init__(
        self,
        message: str | None = None,
        *,
        object_name: str | None = None,
        extra_data: Any = None,
    ) -> None:
        if object_name:
            self.error_title = f"E00002: No such {object_name}."
        super().__init__(message, extra_data=extra_data)

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class GenericBadRequest(BackendAIError):
    """Raised for generic bad request errors."""

    error_type = "https://api.backend.ai/probs/generic-bad-request"
    error_title = "Bad request."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class RejectedByHook(BackendAIError):
    """Raised when operation is rejected by a hook plugin."""

    error_type = "https://api.backend.ai/probs/rejected-by-hook"
    error_title = "Operation rejected by a hook plugin."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.HOOK,
            error_detail=ErrorDetail.FORBIDDEN,
        )

    @classmethod
    def from_hook_result(cls, result: HookResult) -> RejectedByHook:
        return cls(
            result.reason,
            extra_data={
                "plugins": result.src_plugin,
            },
        )


class InvalidCredentials(BackendAIError):
    """Raised when authentication credentials are not valid."""

    error_type = "https://api.backend.ai/probs/invalid-credentials"
    error_title = "Authentication credentials not valid."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.UNAUTHORIZED,
        )


class GenericForbidden(BackendAIError):
    """Raised for generic forbidden operation errors."""

    error_type = "https://api.backend.ai/probs/generic-forbidden"
    error_title = "Forbidden operation."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class InsufficientPrivilege(BackendAIError):
    """Raised when user has insufficient privileges."""

    error_type = "https://api.backend.ai/probs/insufficient-privilege"
    error_title = "Insufficient privilege."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class MethodNotAllowed(BackendAIError):
    """Raised when HTTP method is not allowed."""

    error_type = "https://api.backend.ai/probs/method-not-allowed"
    error_title = "HTTP Method Not Allowed."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class InternalServerError(BackendAIError):
    """Raised for internal server errors."""

    error_type = "https://api.backend.ai/probs/internal-server-error"
    error_title = "Internal server error."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ServerMisconfiguredError(BackendAIError):
    """Raised when server is misconfigured."""

    error_type = "https://api.backend.ai/probs/server-misconfigured"
    error_title = "E00001: Service misconfigured."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class ServiceUnavailable(BackendAIError):
    """Raised when service is unavailable."""

    error_type = "https://api.backend.ai/probs/service-unavailable"
    error_title = "Service unavailable."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class QueryNotImplemented(BackendAIError):
    """Raised when API query is not implemented."""

    error_type = "https://api.backend.ai/probs/not-implemented"
    error_title = "This API query is not implemented."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.NOT_IMPLEMENTED,
        )


class InvalidAuthParameters(BackendAIError):
    """Raised when authorization parameters are missing or invalid."""

    error_type = "https://api.backend.ai/probs/invalid-auth-params"
    error_title = "Missing or invalid authorization parameters."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class AuthorizationFailed(BackendAIError):
    """Raised when credential/signature mismatch occurs."""

    error_type = "https://api.backend.ai/probs/auth-failed"
    error_title = "Credential/signature mismatch."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.UNAUTHORIZED,
        )


class PasswordExpired(BackendAIError):
    """Raised when password has expired."""

    error_type = "https://api.backend.ai/probs/password-expired"
    error_title = "Password has expired."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.DATA_EXPIRED,
        )


class InvalidAPIParameters(BackendAIError):
    """Raised when API parameters are missing or invalid."""

    error_type = "https://api.backend.ai/probs/invalid-api-params"
    error_title = "Missing or invalid API parameters."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class GraphQLError(BackendAIError):
    """Raised for GraphQL-generated errors."""

    error_type = "https://api.backend.ai/probs/graphql-error"
    error_title = "GraphQL-generated error."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.BAD_REQUEST,
        )
