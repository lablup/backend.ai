"""
Circuit-related exceptions for the worker.
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


class InvalidCircuitDataError(BackendAIError):
    """Raised when circuit data is invalid."""

    error_type = "https://api.backend.ai/probs/appproxy-worker/invalid-circuit-data"
    error_title = "Invalid circuit data."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.PARSING,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidFrontendTypeError(BackendAIError):
    """Raised when frontend type is invalid."""

    error_type = "https://api.backend.ai/probs/appproxy-worker/invalid-frontend-type"
    error_title = "Invalid frontend type."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.MISMATCH,
        )


class CircuitNotRegisteredError(BackendAIError, web.HTTPNotFound):
    """Raised when the worker holds no circuit for the slot a request reaches."""

    error_type = "https://api.backend.ai/probs/appproxy-worker/circuit-not-registered"
    error_title = "No circuit is registered for this slot."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.APPPROXY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )
