"""
Web server error classes.
"""

from __future__ import annotations

from typing import override

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class InvalidAPIConfigurationError(BackendAIError, web.HTTPInternalServerError):
    """Raised when API configuration state is invalid."""

    error_type = "https://api.backend.ai/probs/webserver/invalid-api-configuration"
    error_title = "Invalid API configuration state."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.MISMATCH,
        )


class InvalidTemplateValueError(BackendAIError, web.HTTPBadRequest):
    """Raised when template processing encounters invalid values."""

    error_type = "https://api.backend.ai/probs/webserver/invalid-template-value"
    error_title = "Invalid value in template."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.PARSING,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class ManagerConnectionUnavailable(BackendAIError, web.HTTPServiceUnavailable):
    """Raised when no Manager endpoint in the pool is currently healthy."""

    error_type = "https://api.backend.ai/probs/webserver/manager-connection-unavailable"
    error_title = "No healthy Manager endpoint is available."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class UnexpectedAuthResponseError(BackendAIError, web.HTTPInternalServerError):
    """Raised when the Manager returns an unrecognized authorization response type."""

    error_type = "https://api.backend.ai/probs/webserver/unexpected-auth-response"
    error_title = "Unexpected authorization response from the Manager."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
