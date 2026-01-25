"""Base handler class for kernel lifecycle operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Optional

from ai.backend.manager.data.kernel.types import KernelInfo, KernelStatus
from ai.backend.manager.defs import LockID
from ai.backend.manager.sokovan.scheduler.results import (
    KernelExecutionResult,
    KernelStatusTransitions,
)


class KernelLifecycleHandler(ABC):
    """Base class for kernel lifecycle handlers.

    This interface enables the coordinator to:
    1. Query kernels based on target_kernel_statuses()
    2. Execute handler logic with the queried kernels
    3. Apply status transitions based on status_transitions()

    Unlike SessionLifecycleHandler which operates on sessions with kernels,
    KernelLifecycleHandler operates directly on individual kernels.
    """

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        """Get the name of the handler for logging and metrics."""
        raise NotImplementedError("Subclasses must implement name()")

    @classmethod
    @abstractmethod
    def target_kernel_statuses(cls) -> list[KernelStatus]:
        """Get the target kernel statuses for this handler.

        Coordinator queries kernels with these statuses.
        """
        raise NotImplementedError("Subclasses must implement target_kernel_statuses()")

    @classmethod
    @abstractmethod
    def status_transitions(cls) -> KernelStatusTransitions:
        """Define state transitions for kernel handler outcomes.

        Returns:
            KernelStatusTransitions defining what kernel status to transition to for
            success and failure outcomes.

        Note:
            - None in success/failure: Don't change kernel status, only record history
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
        kernels: Sequence[KernelInfo],
    ) -> KernelExecutionResult:
        """Execute the handler logic on the given kernels.

        Args:
            scaling_group: The scaling group being processed
            kernels: Kernels with full KernelInfo data

        Returns:
            Result containing successes and failures for status transitions
        """
        raise NotImplementedError("Subclasses must implement execute()")
