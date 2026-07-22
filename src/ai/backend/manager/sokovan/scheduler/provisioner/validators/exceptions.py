"""Exceptions for validators."""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal
from typing import override

from aiohttp import web

from ai.backend.common.exception import (
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.common.types import SlotName
from ai.backend.manager.sokovan.scheduler.exceptions import SchedulingError


class SchedulingValidationError(SchedulingError, web.HTTPPreconditionFailed):
    """Base exception for validation errors in the Sokovan scheduler.

    Subclasses carry the structured data that describes *what* was violated
    and provide :meth:`summary` so aggregators (e.g.
    :class:`MultipleValidationErrors`) can render a single readable line
    without re-parsing the exception's string representation.
    """

    error_type = "https://api.backend.ai/probs/scheduling-validation-failed"
    error_title = "Scheduling validation failed."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.FORBIDDEN,
        )

    @abstractmethod
    def summary(self) -> str:
        """Return a one-line, human-readable summary of this validation error.

        Used by aggregators to format the error inside a bullet list.
        """
        raise NotImplementedError


def _format_slots(slots: Mapping[SlotName, Decimal]) -> str:
    return " ".join(f"{k}={v}" for k, v in slots.items() if v)


class ConcurrencyLimitExceeded(SchedulingValidationError):
    """Raised when concurrent session limit is exceeded."""

    error_type = "https://api.backend.ai/probs/concurrency-limit-exceeded"
    error_title = "Concurrent session limit exceeded."

    _max_sessions: int
    _session_type: str

    def __init__(self, *, max_sessions: int, session_type: str) -> None:
        self._max_sessions = max_sessions
        self._session_type = session_type
        super().__init__(self.summary())

    @override
    def summary(self) -> str:
        return f"You cannot run more than {self._max_sessions} {self._session_type} sessions"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CHECK_LIMIT,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class DependenciesNotSatisfied(SchedulingValidationError):
    """Raised when session dependencies are not satisfied."""

    error_type = "https://api.backend.ai/probs/dependencies-not-satisfied"
    error_title = "Session dependencies not satisfied."

    _pending_dependency_names: list[str]

    def __init__(self, *, pending_dependency_names: Sequence[str]) -> None:
        self._pending_dependency_names = list(pending_dependency_names)
        super().__init__(self.summary())

    @override
    def summary(self) -> str:
        names = ", ".join(self._pending_dependency_names)
        return f"Waiting dependency sessions to finish as success. ({names})"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CHECK_LIMIT,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class UserResourceQuotaExceeded(SchedulingValidationError):
    """Raised when user resource quota is exceeded."""

    error_type = "https://api.backend.ai/probs/user-resource-quota-exceeded"
    error_title = "User resource quota exceeded."

    _quota_slots: Mapping[SlotName, Decimal]

    def __init__(self, *, quota_slots: Mapping[SlotName, Decimal]) -> None:
        self._quota_slots = quota_slots
        super().__init__(self.summary())

    @override
    def summary(self) -> str:
        return f"Your main-keypair resource quota is exceeded. ({_format_slots(self._quota_slots)})"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.CHECK_LIMIT,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class ProjectResourceQuotaExceeded(SchedulingValidationError):
    """Raised when project resource quota is exceeded."""

    error_type = "https://api.backend.ai/probs/group-resource-quota-exceeded"
    error_title = "Project resource quota exceeded."

    _quota_slots: Mapping[SlotName, Decimal]

    def __init__(self, *, quota_slots: Mapping[SlotName, Decimal]) -> None:
        self._quota_slots = quota_slots
        super().__init__(self.summary())

    @override
    def summary(self) -> str:
        return f"Your project resource quota is exceeded. ({_format_slots(self._quota_slots)})"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.GROUP,
            operation=ErrorOperation.CHECK_LIMIT,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class DomainResourceQuotaExceeded(SchedulingValidationError):
    """Raised when domain resource quota is exceeded."""

    error_type = "https://api.backend.ai/probs/domain-resource-quota-exceeded"
    error_title = "Domain resource quota exceeded."

    _quota_slots: Mapping[SlotName, Decimal]

    def __init__(self, *, quota_slots: Mapping[SlotName, Decimal]) -> None:
        self._quota_slots = quota_slots
        super().__init__(self.summary())

    @override
    def summary(self) -> str:
        return f"Your domain resource quota is exceeded. ({_format_slots(self._quota_slots)})"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DOMAIN,
            operation=ErrorOperation.CHECK_LIMIT,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class ReservedBatchSessionNotReady(SchedulingValidationError):
    """Raised when a batch session has not yet reached its scheduled start time."""

    error_type = "https://api.backend.ai/probs/reserved-batch-session-not-ready"
    error_title = "Reserved batch session is not yet ready to start."

    _scheduled_start: datetime

    def __init__(self, *, scheduled_start: datetime) -> None:
        self._scheduled_start = scheduled_start
        super().__init__(self.summary())

    @override
    def summary(self) -> str:
        return (
            f"Batch session is scheduled to start at {self._scheduled_start.isoformat()};"
            " current time is before that."
        )

    @override
    def error_code(self) -> ErrorCode:
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

    def __init__(self, errors: Sequence[SchedulingValidationError]) -> None:
        self._errors = list(errors)
        super().__init__(self.summary())

    @override
    def summary(self) -> str:
        lines = [f"- {type(e).__name__}: {e.summary()}" for e in self._errors]
        return "Multiple validation errors occurred:\n" + "\n".join(lines)

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.FORBIDDEN,
        )
