"""
Repository-based allocator implementation.

This allocator delegates allocation operations to the schedule repository
to ensure transactional consistency.
"""

from collections.abc import Iterable

from ai.backend.common.types import AgentId
from ai.backend.manager.repositories.schedule.repository import ScheduleRepository
from ai.backend.manager.sokovan.scheduler.types import AllocationBatch, SessionAllocation

from .allocator import SchedulingAllocator


class RepositoryAllocator(SchedulingAllocator):
    """
    Repository-based allocator that delegates to schedule repository.

    This allocator ensures all allocation operations are handled atomically
    by delegating to a single repository method.
    """

    _repository: ScheduleRepository

    def __init__(self, schedule_repository: ScheduleRepository) -> None:
        """
        Initialize the allocator with schedule repository.

        Args:
            schedule_repository: Repository that handles actual allocation
        """
        self._repository = schedule_repository

    async def allocate(self, session_allocations: Iterable[SessionAllocation]) -> None:
        """
        Allocate resources by delegating to repository.

        Args:
            session_allocations: Session allocation decisions to execute
        """
        # Convert to list if needed for multiple iterations
        allocations_list = list(session_allocations)

        # Collect all unique agent IDs from the allocations
        agent_ids: set[AgentId] = set()
        for allocation in allocations_list:
            for kernel_allocation in allocation.kernel_allocations:
                agent_ids.add(kernel_allocation.agent_id)

        # Create allocation batch with collected agent IDs
        allocation_batch = AllocationBatch(
            allocations=allocations_list,
            agent_ids=agent_ids,
        )

        # Delegate to repository for atomic allocation
        await self._repository.allocate_sessions(allocation_batch)
