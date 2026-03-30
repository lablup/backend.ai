"""
Web server error classes.
"""

from __future__ import annotations

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

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.PARSING,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )
