"""
Exceptions for the sokovan scheduler.
"""

from abc import ABC
from typing import override

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class SchedulingError(BackendAIError, ABC):
    """Base exception for scheduling errors.

    All exceptions used in the scheduler must inherit from this class.
    """

    error_type = "https://api.backend.ai/probs/scheduling-failed"
    error_title = "Scheduling failed."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
