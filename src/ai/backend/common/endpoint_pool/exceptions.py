from typing import override

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class NoHealthyEndpointError(BackendAIError, web.HTTPServiceUnavailable):
    error_type = "https://api.backend.ai/probs/no-healthy-endpoint"
    error_title = "No healthy endpoint is available."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.UNAVAILABLE,
        )
