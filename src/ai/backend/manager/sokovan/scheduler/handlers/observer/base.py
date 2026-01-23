"""Base class for kernel observers.

Kernel observers are read-only operations that collect data from kernels
without changing their state. This is different from kernel handlers
which perform status transitions.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass

from ai.backend.manager.data.kernel.types import KernelInfo
from ai.backend.manager.repositories.base import QueryCondition


@dataclass
class ObservationResult:
    """Result of kernel observation for a scaling group."""

    observed_count: int


class KernelObserver(ABC):
    """Base class for kernel observation without state transitions.

    Unlike KernelLifecycleHandler which transitions kernel states,
    KernelObserver only observes and collects data from kernels.
    No status changes are applied.

    Typical use cases:
    - Fair share usage collection
    - Metrics aggregation
    - Resource utilization tracking
    """

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        """Get the name of the observer for logging and metrics."""
        raise NotImplementedError("Subclasses must implement name()")

    @abstractmethod
    def get_query_condition(self, scaling_group: str) -> QueryCondition:
        """Get query condition for kernel filtering.

        Args:
            scaling_group: The scaling group being processed

        Returns:
            QueryCondition for filtering kernels to observe
        """
        raise NotImplementedError("Subclasses must implement get_query_condition()")

    @abstractmethod
    async def observe(
        self,
        scaling_group: str,
        kernels: Sequence[KernelInfo],
    ) -> ObservationResult:
        """Observe the given kernels without changing their state.

        Args:
            scaling_group: The scaling group being processed
            kernels: Kernels with full KernelInfo data

        Returns:
            ObservationResult containing observed count
        """
        raise NotImplementedError("Subclasses must implement observe()")
