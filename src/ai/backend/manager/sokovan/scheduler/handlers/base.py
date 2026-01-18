"""Base handler class for scheduler operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Optional

from ai.backend.manager.data.session.types import StatusTransitions
from ai.backend.manager.defs import LockID
from ai.backend.manager.models.kernel import KernelStatus
from ai.backend.manager.models.session import SessionStatus
from ai.backend.manager.sokovan.scheduler.results import SessionExecutionResult
from ai.backend.manager.sokovan.scheduler.types import SessionWithKernels


class SessionLifecycleHandler(ABC):
    """Base class for session lifecycle handlers following DeploymentCoordinator pattern.

    This interface enables the coordinator to:
    1. Query sessions based on target_statuses() and target_kernel_statuses()
    2. Execute handler logic with the queried sessions
    3. Apply status transitions based on status_transitions() (BEP-1030)

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
    def target_kernel_statuses(cls) -> Optional[list[KernelStatus]]:
        """Get the target kernel statuses for session filtering.

        Sessions are included only if ALL their kernels match these statuses.
        Return None to include sessions regardless of kernel status.
        """
        raise NotImplementedError("Subclasses must implement target_kernel_statuses()")

    @classmethod
    @abstractmethod
    def status_transitions(cls) -> StatusTransitions:
        """Define state transitions for different handler outcomes (BEP-1030).

        Returns:
            StatusTransitions defining what session/kernel status to transition to for
            success, need_retry, expired, and give_up outcomes.

        Note:
            - None in TransitionStatus: Don't change that entity's status
            - None in StatusTransitions field: No status change, only record history
        """
        raise NotImplementedError("Subclasses must implement status_transitions()")

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
        scaling_group: str,
        sessions: Sequence[SessionWithKernels],
    ) -> SessionExecutionResult:
        """Execute the handler logic on the given sessions.

        Args:
            scaling_group: The scaling group being processed
            sessions: Sessions with full SessionInfo and KernelInfo data

        Returns:
            Result containing successes, need_retries, expired, and give_ups for status transitions
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
