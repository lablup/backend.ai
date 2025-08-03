from abc import ABC, abstractmethod
from collections.abc import Iterable

from ai.backend.manager.sokovan.scheduler.types import AllocationSnapshot


class SchedulingAllocator(ABC):
    @abstractmethod
    async def allocate(self, allocation_snapshots: Iterable[AllocationSnapshot]) -> None:
        """
        Allocate resources based on the provided allocation snapshots.

        Args:
            allocation_snapshots: Iterable of AllocationSnapshot objects
        """
        raise NotImplementedError("Subclasses must implement this method.")
