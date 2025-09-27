from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

from ai.backend.common.bgtask.task.base import BaseBackgroundTaskResult

from ..events.event_types.bgtask.broadcast import (
    BaseBgtaskDoneEvent,
    BgtaskCancelledEvent,
    BgtaskDoneEvent,
    BgtaskFailedEvent,
)
from ..exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from .types import BgtaskStatus

R = TypeVar("R", bound=BaseBackgroundTaskResult)


class TaskResult(ABC):
    """Abstract base class for task execution results."""

    @abstractmethod
    def to_broadcast_event(self, task_id: uuid.UUID) -> BaseBgtaskDoneEvent:
        """Convert the task result to a broadcast event."""
        raise NotImplementedError

    @abstractmethod
    def status(self) -> BgtaskStatus:
        """Get the background task status."""
        raise NotImplementedError

    @abstractmethod
    def error_code(self) -> Optional[ErrorCode]:
        """Get the error code if applicable."""
        raise NotImplementedError


@dataclass
class TaskSuccessResult(TaskResult, Generic[R]):
    """Successful task execution result."""

    result: R

    def to_broadcast_event(self, task_id: uuid.UUID) -> BaseBgtaskDoneEvent:
        # For now, convert the result to string for the message
        # This assumes the result has a meaningful string representation
        message = (
            str(self.result.serialize())
            if self.result is not None
            else "Task completed successfully"
        )
        return BgtaskDoneEvent(task_id=task_id, message=message)

    def status(self) -> BgtaskStatus:
        return BgtaskStatus.DONE

    def error_code(self) -> Optional[ErrorCode]:
        return None


@dataclass
class TaskCancelledResult(TaskResult):
    """Cancelled task execution result."""

    message: str = "Task cancelled"

    def to_broadcast_event(self, task_id: uuid.UUID) -> BaseBgtaskDoneEvent:
        return BgtaskCancelledEvent(task_id, self.message)

    def status(self) -> BgtaskStatus:
        return BgtaskStatus.CANCELLED

    def error_code(self) -> Optional[ErrorCode]:
        return ErrorCode(
            domain=ErrorDomain.BGTASK,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.CANCELED,
        )


@dataclass
class TaskFailedResult(TaskResult):
    """Failed task execution result."""

    exception: BaseException

    def to_broadcast_event(self, task_id: uuid.UUID) -> BaseBgtaskDoneEvent:
        return BgtaskFailedEvent(task_id, repr(self.exception))

    def status(self) -> BgtaskStatus:
        return BgtaskStatus.FAILED

    def error_code(self) -> Optional[ErrorCode]:
        if isinstance(self.exception, BackendAIError):
            return self.exception.error_code()
        else:
            return ErrorCode(
                domain=ErrorDomain.BGTASK,
                operation=ErrorOperation.EXECUTE,
                error_detail=ErrorDetail.INTERNAL_ERROR,
            )
