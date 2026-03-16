from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class NoUserUpdateError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/no-update-error"
    error_title = "No update user fields provided."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.BAD_REQUEST,
        )
