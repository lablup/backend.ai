"""
Exceptions for the sokovan scheduler.
"""

from abc import ABC, abstractmethod

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.sokovan.scheduler.types import SchedulingPredicate


class SchedulingError(BackendAIError, ABC):
    """Base exception for scheduling errors.

    All exceptions used in the scheduler must inherit from this class
    and implement the failed_predicates method.
    """

    error_type = "https://api.backend.ai/probs/scheduling-failed"
    error_title = "Scheduling failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )

    @abstractmethod
    def failed_predicates(self) -> list[SchedulingPredicate]:
        """Return list of failed predicates for this error.

        Returns:
            List of SchedulingPredicate objects.
        """
        raise NotImplementedError
