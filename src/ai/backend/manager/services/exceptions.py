from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class BaseServiceException(BackendAIError):
    """Base exception for all service-related errors."""

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.SERVICE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
