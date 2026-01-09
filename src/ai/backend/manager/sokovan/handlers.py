"""
Base handler class for schedule and deployment operations.
"""

from abc import ABC, abstractmethod
from typing import Optional

from ai.backend.manager.defs import LockID
from ai.backend.manager.sokovan.base import SokovanHandler
from ai.backend.manager.sokovan.scheduler.results import ScheduleResult

__all__ = [
    "ScheduleHandler",
    "SchedulerHandler",
]


class ScheduleHandler(ABC):
    """Base class for schedule operation handlers (legacy, kept for compatibility)."""

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        raise NotImplementedError("Subclasses must implement name()")

    @property
    @abstractmethod
    def lock_id(self) -> Optional[LockID]:
        """Get the lock ID for this handler.

        Returns:
            LockID to acquire before execution, or None if no lock needed
        """
        raise NotImplementedError("Subclasses must implement lock_id")

    @abstractmethod
    async def execute(self) -> ScheduleResult:
        """Execute the scheduling operation.

        Returns:
            Result of the scheduling operation
        """
        raise NotImplementedError("Subclasses must implement execute()")

    @abstractmethod
    async def post_process(self, result: ScheduleResult) -> None:
        """Handle post-processing after the operation.

        Args:
            result: The result from execute()
        """
        raise NotImplementedError("Subclasses must implement post_process()")


class SchedulerHandler(SokovanHandler[ScheduleResult], ABC):
    """Base class for scheduler operation handlers using the generic interface."""
