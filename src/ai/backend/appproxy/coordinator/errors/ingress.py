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


class ApiDeliveryWorkerRequestError(BackendAIError, web.HTTPBadGateway):
    """Raised when an api-delivery worker cannot be reached or answers a request with an error."""

    error_type = (
        "https://api.backend.ai/probs/appproxy-coordinator/api-delivery-worker-request-failed"
    )
    error_title = "A request to an api-delivery worker failed."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.APPPROXY,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.UNREACHABLE,
        )
