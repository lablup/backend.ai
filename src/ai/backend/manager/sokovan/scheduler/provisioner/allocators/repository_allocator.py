"""
Repository-based allocator implementation.

This allocator delegates allocation operations to the schedule repository
to ensure transactional consistency.
"""

from ai.backend.manager.repositories.scheduler import SchedulerRepository
from ai.backend.manager.sokovan.scheduler.results import ScheduledSessionData
from ai.backend.manager.sokovan.scheduler.types import AllocationBatch

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

    async def allocate(self, batch: AllocationBatch) -> list[ScheduledSessionData]:
        """
        Allocate resources by delegating to repository and update session status.
        Both allocations and failures are processed in a single transaction.

        Args:
            batch: AllocationBatch containing allocations and failures to process

        Returns:
            List of ScheduledSessionData for allocated sessions
        """
        # Delegate to repository for atomic processing of both allocations and failures
        return await self._repository.allocate_sessions(batch)
