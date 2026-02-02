from __future__ import annotations

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class AppProxyConnectionError(BackendAIError, web.HTTPServiceUnavailable):
    """Raised when connection to AppProxy fails."""

    error_type = "https://api.backend.ai/probs/appproxy-connection-error"
    error_title = "Failed to connect to AppProxy."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.APPPROXY,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class AppProxyResponseError(BackendAIError, web.HTTPInternalServerError):
    """Raised when AppProxy returns an invalid response."""

    error_type = "https://api.backend.ai/probs/appproxy-response-error"
    error_title = "Invalid response from AppProxy."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.APPPROXY,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.INVALID_DATA_FORMAT,
        )
