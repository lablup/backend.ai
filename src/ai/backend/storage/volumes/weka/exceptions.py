"""
Weka-specific exceptions.
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


class WekaError(BackendAIError, web.HTTPInternalServerError):
    """Base class for Weka errors."""

    error_type = "https://api.backend.ai/probs/storage/weka/generic"
    error_title = "Weka Error"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class WekaInitError(WekaError):
    """Raised when Weka initialization fails."""

    error_type = "https://api.backend.ai/probs/storage/weka/init-error"
    error_title = "Weka Initialization Error"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class WekaAPIError(WekaError):
    """Base class for Weka API errors."""

    error_type = "https://api.backend.ai/probs/storage/weka/api-error"
    error_title = "Weka API Error"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.UNREACHABLE,
        )


class WekaInvalidBodyError(WekaAPIError, web.HTTPBadRequest):
    """Raised when a Weka API request has an invalid body."""

    error_type = "https://api.backend.ai/probs/storage/weka/invalid-body"
    error_title = "Weka Invalid Body"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class WekaUnauthorizedError(WekaAPIError):
    """Raised when a Weka API request is unauthorized."""

    error_type = "https://api.backend.ai/probs/storage/weka/unauthorized"
    error_title = "Weka Unauthorized"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.UNAUTHORIZED,
        )


class WekaNotFoundError(WekaAPIError, web.HTTPNotFound):
    """Raised when a Weka resource is not found."""

    error_type = "https://api.backend.ai/probs/storage/weka/not-found"
    error_title = "Weka Not Found"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class WekaInternalError(WekaAPIError):
    """Raised when a Weka internal error occurs."""

    error_type = "https://api.backend.ai/probs/storage/weka/internal-error"
    error_title = "Weka Internal Error"


class WekaNoMetricError(WekaError, web.HTTPNotFound):
    """Raised when Weka metrics are not available."""

    error_type = "https://api.backend.ai/probs/storage/weka/no-metric"
    error_title = "Weka No Metric"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )
