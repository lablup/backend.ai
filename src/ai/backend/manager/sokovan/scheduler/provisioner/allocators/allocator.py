from abc import ABC, abstractmethod

from ai.backend.common.types import SessionId
from ai.backend.manager.views.sokovan.allocation import AllocationBatch


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
    async def allocate(self, batch: AllocationBatch) -> list[SessionId]:
        """
        Reserve and assign the batch's sessions to agents atomically.

        Args:
            batch: AllocationBatch containing the successful allocations to process

        Returns:
            The ids of the sessions that were actually allocated.
        """
        raise NotImplementedError("Subclasses must implement this method.")
