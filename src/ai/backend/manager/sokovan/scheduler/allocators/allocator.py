from abc import ABC, abstractmethod
from collections.abc import Iterable

from ai.backend.manager.sokovan.scheduler.types import SchedulingFailure, SessionAllocation


class SchedulingAllocator(ABC):
    @abstractmethod
    async def allocate(
        self,
        session_allocations: Iterable[SessionAllocation],
        scheduling_failures: Iterable[SchedulingFailure] | None = None,
    ) -> None:
        """
        Allocate resources based on the provided session allocations and handle failures.
        This method should handle the actual resource allocation logic,
        ensuring that all allocations are performed atomically and consistently.
        It also updates session status for both successful allocations and failures.

        Args:
            session_allocations: Iterable of SessionAllocation objects
            scheduling_failures: Optional iterable of SchedulingFailure objects for failed sessions
        """
        raise NotImplementedError("Subclasses must implement this method.")
