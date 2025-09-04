"""Exceptions for validators."""

from aiohttp import web

from ai.backend.common.exception import (
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.sokovan.scheduler.exceptions import SchedulingError
from ai.backend.manager.sokovan.scheduler.types import SchedulingPredicate


class SchedulingValidationError(SchedulingError, web.HTTPPreconditionFailed):
    """Base exception for validation errors in the Sokovan scheduler."""

    error_type = "https://api.backend.ai/probs/scheduling-validation-failed"
    error_title = "Scheduling validation failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.FORBIDDEN,
        )

    def failed_predicates(self) -> list[SchedulingPredicate]:
        """Return list of failed predicates for this error."""
        return [SchedulingPredicate(name=type(self).__name__, msg=str(self))]


class ConcurrencyLimitExceeded(SchedulingValidationError):
    """Raised when concurrent session limit is exceeded."""

    error_type = "https://api.backend.ai/probs/concurrency-limit-exceeded"
    error_title = "Concurrent session limit exceeded."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CHECK_LIMIT,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class DependenciesNotSatisfied(SchedulingValidationError):
    """Raised when session dependencies are not satisfied."""

    error_type = "https://api.backend.ai/probs/dependencies-not-satisfied"
    error_title = "Session dependencies not satisfied."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CHECK_LIMIT,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class KeypairResourceQuotaExceeded(SchedulingValidationError):
    """Raised when keypair resource quota is exceeded."""

    error_type = "https://api.backend.ai/probs/keypair-resource-quota-exceeded"
    error_title = "Keypair resource quota exceeded."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KEYPAIR,
            operation=ErrorOperation.CHECK_LIMIT,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class UserResourceQuotaExceeded(SchedulingValidationError):
    """Raised when user resource quota is exceeded."""

    error_type = "https://api.backend.ai/probs/user-resource-quota-exceeded"
    error_title = "User resource quota exceeded."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.CHECK_LIMIT,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class GroupResourceQuotaExceeded(SchedulingValidationError):
    """Raised when group resource quota is exceeded."""

    error_type = "https://api.backend.ai/probs/group-resource-quota-exceeded"
    error_title = "Group resource quota exceeded."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.GROUP,
            operation=ErrorOperation.CHECK_LIMIT,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class DomainResourceQuotaExceeded(SchedulingValidationError):
    """Raised when domain resource quota is exceeded."""

    error_type = "https://api.backend.ai/probs/domain-resource-quota-exceeded"
    error_title = "Domain resource quota exceeded."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DOMAIN,
            operation=ErrorOperation.CHECK_LIMIT,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class PendingSessionCountLimitExceeded(SchedulingValidationError):
    """Raised when pending session count limit is exceeded."""

    error_type = "https://api.backend.ai/probs/pending-session-count-limit-exceeded"
    error_title = "Pending session count limit exceeded."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CHECK_LIMIT,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class PendingSessionResourceLimitExceeded(SchedulingValidationError):
    """Raised when pending session resource limit is exceeded."""

    error_type = "https://api.backend.ai/probs/pending-session-resource-limit-exceeded"
    error_title = "Pending session resource limit exceeded."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CHECK_LIMIT,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class MultipleValidationErrors(SchedulingValidationError):
    """Raised when multiple validation errors occur."""

    error_type = "https://api.backend.ai/probs/multiple-validation-errors"
    error_title = "Multiple validation errors occurred."

    _errors: list[SchedulingValidationError]

    def __init__(self, errors: list[SchedulingValidationError]) -> None:
        """
        Initialize with a list of validation errors.

        Args:
            errors: List of validation errors that occurred
        """
        self._errors = errors
        # Format each error on a new line for better readability
        messages = []
        for i, e in enumerate(errors, 1):
            error_name = type(e).__name__
            error_msg = str(e)
            messages.append(f"  {i}. {error_name}: {error_msg}")

        # Join with newlines for better formatting
        formatted_errors = "\n".join(messages)
        super().__init__(f"Multiple validation errors occurred:\n{formatted_errors}")

    def failed_predicates(self) -> list[SchedulingPredicate]:
        """Return list of all failed predicates from all errors."""
        predicates = []
        for error in self._errors:
            predicates.extend(error.failed_predicates())
        return predicates

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.FORBIDDEN,
        )
