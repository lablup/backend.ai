from abc import ABC, abstractmethod

from ai.backend.manager.sokovan.scheduler.results import ScheduledSessionData
from ai.backend.manager.sokovan.scheduler.types import AllocationBatch


class SchedulingAllocator(ABC):
    @abstractmethod
    def name(self) -> str:
        """
        Return the allocator name for predicates.
        """
        raise NotImplementedError

    @abstractmethod
    def success_message(self) -> str:
        """
        Return a message describing successful allocation.
        """
        raise NotImplementedError

    @abstractmethod
    async def allocate(self, batch: AllocationBatch) -> list[ScheduledSessionData]:
        """
        Allocate resources based on the provided allocation batch.
        This method should handle the actual resource allocation logic,
        ensuring that all allocations are performed atomically and consistently.
        It also updates session status for both successful allocations and failures.

        Args:
            batch: AllocationBatch containing successful allocations and failures to process

        Returns:
            List of ScheduledSessionData for allocated sessions
        """
        raise NotImplementedError("Subclasses must implement this method.")
