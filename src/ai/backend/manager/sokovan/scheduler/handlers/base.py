"""Base handler class for scheduler operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Optional

from ai.backend.manager.defs import LockID
from ai.backend.manager.models.kernel import KernelStatus
from ai.backend.manager.models.session import SessionStatus
from ai.backend.manager.sokovan.scheduler.results import (
    HandlerSessionData,
    ScheduleResult,
    SessionExecutionResult,
)


class SchedulerHandler(ABC):
    """Base class for scheduler operation handlers (legacy interface)."""

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


class SessionLifecycleHandler(ABC):
    """Base class for session lifecycle handlers following DeploymentCoordinator pattern.

    This interface enables the coordinator to:
    1. Query sessions based on target_statuses() and target_kernel_statuses()
    2. Execute handler logic with the queried sessions
    3. Apply status transitions based on success_status(), failure_status(), stale_status()

    Handlers can:
    - Perform additional data queries if needed (Option B-1)
    - Execute hooks for lifecycle transitions
    - Call Scheduler methods for core business logic
    """

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        """Get the name of the handler for logging and metrics."""
        raise NotImplementedError("Subclasses must implement name()")

    @classmethod
    @abstractmethod
    def target_statuses(cls) -> list[SessionStatus]:
        """Get the target session statuses for this handler.

        Coordinator queries sessions with these statuses.
        """
        raise NotImplementedError("Subclasses must implement target_statuses()")

    @classmethod
    @abstractmethod
    def target_kernel_statuses(cls) -> list[KernelStatus]:
        """Get the target kernel statuses for session filtering.

        Sessions are included only if ALL their kernels match these statuses.
        Return empty list [] to include sessions regardless of kernel status.
        """
        raise NotImplementedError("Subclasses must implement target_kernel_statuses()")

    @classmethod
    @abstractmethod
    def success_status(cls) -> Optional[SessionStatus]:
        """Get the status to set on successful execution.

        Returns:
            SessionStatus to set for successes, or None if coordinator should not update status
        """
        raise NotImplementedError("Subclasses must implement success_status()")

    @classmethod
    @abstractmethod
    def failure_status(cls) -> Optional[SessionStatus]:
        """Get the status to set on failed execution.

        Returns:
            SessionStatus to set for failures, or None if coordinator should not update status
        """
        raise NotImplementedError("Subclasses must implement failure_status()")

    @classmethod
    @abstractmethod
    def stale_status(cls) -> Optional[SessionStatus]:
        """Get the status to set for stale/timeout sessions.

        Returns:
            SessionStatus to set for stales, or None if coordinator should not update status
        """
        raise NotImplementedError("Subclasses must implement stale_status()")

    @property
    @abstractmethod
    def lock_id(self) -> Optional[LockID]:
        """Get the lock ID for this handler.

        Returns:
            LockID to acquire before execution, or None if no lock needed
        """
        raise NotImplementedError("Subclasses must implement lock_id")

    @abstractmethod
    async def execute(
        self,
        sessions: Sequence[HandlerSessionData],
        scaling_group: str,
    ) -> SessionExecutionResult:
        """Execute the handler logic on the given sessions.

        Args:
            sessions: Sessions queried by coordinator based on target_statuses()
            scaling_group: The scaling group being processed

        Returns:
            Result containing successes, failures, and stales for status transitions
        """
        raise NotImplementedError("Subclasses must implement execute()")

    @abstractmethod
    async def post_process(self, result: SessionExecutionResult) -> None:
        """Handle post-processing after the operation.

        Typically includes:
        - Broadcasting events for status transitions
        - Invalidating caches for affected access keys
        - Requesting next scheduling phase

        Args:
            result: The result from execute()
        """
        raise NotImplementedError("Subclasses must implement post_process()")
