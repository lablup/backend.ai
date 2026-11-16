"""
Circuit-related exceptions for the worker.
"""

from __future__ import annotations

<<<<<<< HEAD
=======
from typing import override

from aiohttp import web

>>>>>>> f7d925561 (fix(BA-9045): give every AppProxy error class an HTTP status (#17125))
from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class InvalidCircuitDataError(BackendAIError, web.HTTPInternalServerError):
    """Raised when circuit data is invalid."""

    error_type = "https://api.backend.ai/probs/appproxy-worker/invalid-circuit-data"
    error_title = "Invalid circuit data."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.PARSING,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidFrontendTypeError(BackendAIError, web.HTTPInternalServerError):
    """Raised when frontend type is invalid."""

    error_type = "https://api.backend.ai/probs/appproxy-worker/invalid-frontend-type"
    error_title = "Invalid frontend type."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.MISMATCH,
        )
