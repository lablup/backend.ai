"""
Repository-based allocator implementation.

This allocator delegates allocation operations to the schedule repository
to ensure transactional consistency.
"""

from ai.backend.common.types import SessionId
from ai.backend.manager.repositories.scheduler import SchedulerRepository
from ai.backend.manager.sokovan.data import AllocationBatch

from .allocator import SchedulingAllocator


class RepositoryAllocator(SchedulingAllocator):
    """
    Repository-based allocator that delegates to schedule repository.

    This allocator ensures all allocation operations are handled atomically
    by delegating to a single repository method.
    """

    _repository: SchedulerRepository

    def name(self) -> str:
        """
        Return the allocator name for predicates.
        """
        return "RepositoryAllocator"

    def success_message(self) -> str:
        """
        Return a message describing successful allocation.
        """
        return "Resources successfully allocated to agents"

    def __init__(self, schedule_repository: SchedulerRepository) -> None:
        """
        Initialize the allocator with schedule repository.

        Args:
            schedule_repository: Repository that handles actual allocation
        """
        self._repository = schedule_repository

    async def allocate(self, batch: AllocationBatch) -> list[SessionId]:
        """
        Reserve and assign the batch's sessions to agents by delegating to the
        repository (single atomic transaction).

        Args:
            batch: AllocationBatch containing the allocations to process

        Returns:
            The ids of the sessions that were actually allocated.
        """
        return await self._repository.allocate_sessions(batch)
