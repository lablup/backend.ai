"""Base handler class for session promotion operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Optional

from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import (
    KernelMatchType,
    SessionInfo,
    SessionStatus,
    StatusTransitions,
)
from ai.backend.manager.defs import LockID
from ai.backend.manager.sokovan.scheduler.results import SessionExecutionResult


class SessionPromotionHandler(ABC):
    """Base class for session promotion handlers.

    Promotion handlers check kernel status conditions to determine
    if a session should be promoted (or demoted) to a new status.

    Key differences from SessionLifecycleHandler:
    - target_kernel_statuses() is required (non-optional)
    - kernel_match_type() defines ALL/ANY/NOT_ANY condition
    - No failure_status() or stale_status() (promotion is success or wait)

    The coordinator will:
    1. Query sessions based on target_statuses()
    2. Filter sessions based on target_kernel_statuses() and kernel_match_type()
    3. Execute handler logic with filtered sessions
    4. Apply status transition from success_status() for successes
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
        """Get the target kernel statuses for condition checking.

        Unlike SessionLifecycleHandler, this is required for promotion handlers
        as the kernel status condition is the primary trigger for promotion.
        """
        raise NotImplementedError("Subclasses must implement target_kernel_statuses()")

    @classmethod
    @abstractmethod
    def kernel_match_type(cls) -> KernelMatchType:
        """Get the kernel match type for filtering sessions.

        Returns:
            KernelMatchType.ALL: All kernels must match target_kernel_statuses
            KernelMatchType.ANY: At least one kernel must match
            KernelMatchType.NOT_ANY: No kernel should match
        """
        raise NotImplementedError("Subclasses must implement kernel_match_type()")

    @classmethod
    @abstractmethod
    def success_status(cls) -> SessionStatus:
        """Get the status to set on successful execution.

        Unlike SessionLifecycleHandler, this is required for promotion handlers
        as every successful promotion must result in a status change.
        """
        raise NotImplementedError("Subclasses must implement success_status()")

    @classmethod
    @abstractmethod
    def status_transitions(cls) -> StatusTransitions:
        """Define state transitions for different handler outcomes (BEP-1030).

        For promotion handlers, typically only success transition is defined.
        need_retry, expired, give_up are usually None for promotion handlers.

        Returns:
            StatusTransitions defining what session/kernel status to transition to.
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
        sessions: Sequence[SessionInfo],
    ) -> SessionExecutionResult:
        """Execute the promotion logic on the given sessions.

        Args:
            scaling_group: The scaling group being processed
            sessions: Sessions matching the kernel match condition (session data only)

        Returns:
            Result containing successes for status transitions.
            Failures and stales are not typically used for promotion handlers.
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
