"""
Repository-based allocator implementation.

This allocator delegates allocation operations to the schedule repository
to ensure transactional consistency.
"""

from collections.abc import Iterable
from typing import TYPE_CHECKING

from ai.backend.manager.sokovan.scheduler.types import AllocationSnapshot

from .allocator import SchedulingAllocator

if TYPE_CHECKING:
    from ai.backend.manager.repositories.schedule.repository import ScheduleRepository


class RepositoryAllocator(SchedulingAllocator):
    """
    Repository-based allocator that delegates to schedule repository.

    This allocator ensures all allocation operations are handled atomically
    by delegating to a single repository method.
    """

    def __init__(self, schedule_repository: "ScheduleRepository") -> None:
        """
        Initialize the allocator with schedule repository.

        Args:
            schedule_repository: Repository that handles actual allocation
        """
        self.schedule_repository = schedule_repository

    async def allocate(self, allocation_snapshots: Iterable[AllocationSnapshot]) -> None:
        """
        Allocate resources by delegating to repository.

        Args:
            allocation_snapshots: Allocation decisions to execute
        """
        # TODO: This method should be implemented in ScheduleRepository
        await self.schedule_repository.allocate_sessions(allocation_snapshots)  # type: ignore[attr-defined]
