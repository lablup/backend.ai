from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class UnauthorizedPurityClient(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/purity-unauthorized-client"
    error_title = "Unauthorized Purity Client"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.UNAUTHORIZED,
        )
