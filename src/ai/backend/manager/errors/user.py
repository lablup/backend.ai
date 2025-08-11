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


class UserConflict(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/user-conflict"
    error_title = "The user already exists."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class UserCreationBadRequest(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/user-creation-bad-request"
    error_title = "Failed to create user due to bad request."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class UserCreationFailure(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/user-creation-failure"
    error_title = "Failed to create user."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class UserModificationFailure(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/user-modification-failure"
    error_title = "Failed to modify user."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class UserPurgeFailure(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/user-purge-failure"
    error_title = "Failed to purge user."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.HARD_DELETE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
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
