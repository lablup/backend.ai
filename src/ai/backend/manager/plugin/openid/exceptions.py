from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class InvalidSession(BackendAIError, web.HTTPUnauthorized):
    error_type = "https://api.backend.ai/probs/invalid-openid-session"
    error_title = "The OpenID session is invalid or has expired."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.UNAUTHORIZED,
        )
