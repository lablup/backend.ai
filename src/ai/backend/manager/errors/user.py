from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class UserNotFound(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/user-not-found"
    error_title = "The user does not exist."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class KeyPairNotFound(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/keypair-not-found"
    error_title = "The key pair does not exist."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KEYPAIR,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class KeyPairForbidden(BackendAIError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/keypair-forbidden"
    error_title = "The key pair is not allowed to be used."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KEYPAIR,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.FORBIDDEN,
        )
