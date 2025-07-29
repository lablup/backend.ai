"""
Scheduler-related exceptions.
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


class SchedulerValidationError(BackendAIError, web.HTTPPreconditionFailed):
    """Base exception for scheduler validation errors"""

    error_type = "https://api.backend.ai/probs/scheduler-validation-failed"
    error_title = "Scheduler validation failed"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SCHEDULER,
            operation=ErrorOperation.VALIDATE,
            error_detail=ErrorDetail.PRECONDITION_FAILED,
        )


class ReservedBatchSessionError(SchedulerValidationError):
    """Raised when batch session is scheduled before its start time"""

    error_type = "https://api.backend.ai/probs/reserved-batch-session"
    error_title = "Batch session cannot start before scheduled time"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SCHEDULER,
            operation=ErrorOperation.VALIDATE,
            error_detail=ErrorDetail.PRECONDITION_FAILED,
        )


class ConcurrencyLimitError(SchedulerValidationError):
    """Raised when concurrent session limit is exceeded"""

    error_type = "https://api.backend.ai/probs/concurrency-limit-exceeded"
    error_title = "Concurrent session limit exceeded"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SCHEDULER,
            operation=ErrorOperation.VALIDATE,
            error_detail=ErrorDetail.QUOTA_EXCEEDED,
        )


class DependencyNotMetError(SchedulerValidationError):
    """Raised when session dependencies are not satisfied"""

    error_type = "https://api.backend.ai/probs/dependency-not-met"
    error_title = "Session dependencies not satisfied"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SCHEDULER,
            operation=ErrorOperation.VALIDATE,
            error_detail=ErrorDetail.DEPENDENCY_ERROR,
        )


class ResourceQuotaExceededError(SchedulerValidationError):
    """Raised when resource quota is exceeded"""

    error_type = "https://api.backend.ai/probs/resource-quota-exceeded"
    error_title = "Resource quota exceeded"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SCHEDULER,
            operation=ErrorOperation.VALIDATE,
            error_detail=ErrorDetail.QUOTA_EXCEEDED,
        )


class PendingSessionLimitError(SchedulerValidationError):
    """Raised when pending session limit is exceeded"""

    error_type = "https://api.backend.ai/probs/pending-session-limit-exceeded"
    error_title = "Pending session limit exceeded"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SCHEDULER,
            operation=ErrorOperation.VALIDATE,
            error_detail=ErrorDetail.QUOTA_EXCEEDED,
        )
