"""
Session-related exceptions.
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


class SessionCreationFailed(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/session-creation-failed"
    error_title = "Session creation failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.UNSPECIFIED,
        )


class SessionUpdateFailed(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/session-update-failed"
    error_title = "Session update failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.UNSPECIFIED,
        )


class SessionDeletionFailed(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/session-deletion-failed"
    error_title = "Session deletion failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.DELETE,
            error_detail=ErrorDetail.UNSPECIFIED,
        )


class SessionInvalidParameter(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/session-invalid-parameter"
    error_title = "Invalid parameter for session operation."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class SessionAlreadyTerminated(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/session-already-terminated"
    error_title = "Session is already terminated."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )


class SessionNameDuplicate(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/session-name-duplicate"
    error_title = "Session name already exists."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )
