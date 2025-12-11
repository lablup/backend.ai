"""
Authentication-related exceptions for the worker.
"""

from __future__ import annotations

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class ClientIPNotAvailableError(BackendAIError):
    """Raised when client IP address is not available in the request."""

    error_type = "https://api.backend.ai/probs/appproxy-worker/client-ip-not-available"
    error_title = "Client IP not available."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidClientIPFormatError(BackendAIError):
    """Raised when client IP address format is invalid."""

    error_type = "https://api.backend.ai/probs/appproxy-worker/invalid-client-ip-format"
    error_title = "Invalid client IP format."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.PARSING,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class ClientIPNotAllowedError(BackendAIError):
    """Raised when client IP is not in the allowed list."""

    error_type = "https://api.backend.ai/probs/appproxy-worker/client-ip-not-allowed"
    error_title = "Client IP not allowed."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.FORBIDDEN,
        )
