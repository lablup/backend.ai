"""
Exceptions for the sokovan scheduler.
"""

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class SchedulingError(BackendAIError):
    """Base exception for scheduling errors."""

    error_type = "https://api.backend.ai/probs/scheduling-failed"
    error_title = "Scheduling failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class NoResourceRequirementsError(SchedulingError):
    """Raised when no resource requirements are found for a session."""

    error_type = "https://api.backend.ai/probs/no-resource-requirements"
    error_title = "No resource requirements found for session."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidAllocationError(SchedulingError):
    """Raised when allocation is invalid or inconsistent."""

    error_type = "https://api.backend.ai/probs/invalid-allocation"
    error_title = "Invalid resource allocation."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
