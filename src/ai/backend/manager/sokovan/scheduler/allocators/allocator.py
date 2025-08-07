from abc import ABC, abstractmethod
from collections.abc import Iterable

from ai.backend.manager.sokovan.scheduler.types import SessionAllocation


class SchedulingAllocator(ABC):
    @abstractmethod
    async def allocate(self, session_allocations: Iterable[SessionAllocation]) -> None:
        """
        Allocate resources based on the provided session allocations.
        This method should handle the actual resource allocation logic,
        ensuring that all allocations are performed atomically and consistently.

        Args:
            session_allocations: Iterable of SessionAllocation objects
        """
        raise NotImplementedError("Subclasses must implement this method.")
