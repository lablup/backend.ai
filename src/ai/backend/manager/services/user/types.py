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

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.BAD_REQUEST,
        )
