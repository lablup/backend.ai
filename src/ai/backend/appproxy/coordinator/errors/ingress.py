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


class ApiDeliveryWorkerUnreachableError(BackendAIError, web.HTTPBadGateway):
    """Raised when an api-delivery worker cannot be reached."""

    error_type = "https://api.backend.ai/probs/appproxy-coordinator/api-delivery-worker-unreachable"
    error_title = "An api-delivery worker cannot be reached."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.APPPROXY,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.UNREACHABLE,
        )


class ApiDeliveryWorkerRejectedError(BackendAIError, web.HTTPBadRequest):
    """Raised when an api-delivery worker answers a request with a 4xx."""

    error_type = "https://api.backend.ai/probs/appproxy-coordinator/api-delivery-worker-rejected"
    error_title = "An api-delivery worker rejected the request."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.APPPROXY,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class ApiDeliveryWorkerServerError(BackendAIError, web.HTTPBadGateway):
    """Raised when an api-delivery worker answers a request with a 5xx."""

    error_type = (
        "https://api.backend.ai/probs/appproxy-coordinator/api-delivery-worker-server-error"
    )
    error_title = "An api-delivery worker failed to handle the request."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.APPPROXY,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
