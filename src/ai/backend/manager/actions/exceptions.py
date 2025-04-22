from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class BaseActionException(BackendAIError):
    """Base exception for all action-related errors."""

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.SERVICE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
