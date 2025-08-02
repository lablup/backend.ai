from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

from ai.backend.common.types import AccessKey, ResourceSlot
from ai.backend.manager.sokovan.scheduler.allocators.allocator import (
    AllocationSnapshot,
    ResourceAllocator,
)
from ai.backend.manager.sokovan.scheduler.prioritizers.prioritizer import SchedulingPrioritizer
from ai.backend.manager.sokovan.scheduler.types import SessionWorkload, SystemSnapshot
from ai.backend.manager.sokovan.scheduler.validators.validator import SchedulingValidator


class SchedulerRepository(Protocol):
    """Protocol for repository to fetch system state for scheduling."""

    async def get_total_capacity(self) -> ResourceSlot:
        """Get total resource capacity of the system."""
        ...

    async def get_user_allocations(self) -> Mapping[AccessKey, ResourceSlot]:
        """Get current resource allocations per user."""
        ...

    # TODO: Replace above methods with a single method that returns all scheduling data
    # async def get_scheduling_data(self) -> SchedulingData:
    #     """Get all data needed for scheduling in a single call."""
    #     ...


@dataclass
class SchedulerArgs:
    validator: SchedulingValidator
    allocator: ResourceAllocator
    prioritizer: SchedulingPrioritizer
    repository: SchedulerRepository


class Scheduler:
    _prioritizer: SchedulingPrioritizer
    _validator: SchedulingValidator
    _allocator: ResourceAllocator
    _repository: SchedulerRepository

    def __init__(self, args: SchedulerArgs) -> None:
        self._prioritizer = args.prioritizer
        self._validator = args.validator
        self._allocator = args.allocator
        self._repository = args.repository

    async def enqueue(self, workload: SessionWorkload) -> None:
        """
        Enqueue a session workload for scheduling.
        This method should be called to add a new session workload to the scheduler's queue.
        """
        ...

    async def _schedule_queued_sessions(self, workload: Sequence[SessionWorkload]) -> None:
        """
        Schedule all queued sessions by prioritizing them and applying the scheduling policy.
        :param workload: A sequence of SessionWorkload objects to be scheduled.
        """
        # Fetch system state from repository
        total_capacity = await self._repository.get_total_capacity()
        user_allocations = await self._repository.get_user_allocations()

        # Create system snapshot
        system_snapshot = SystemSnapshot(
            total_capacity=total_capacity,
            user_allocations=user_allocations,
        )

        # TODO: In the future, this will be refactored to:
        # scheduling_data = await self._repository.get_scheduling_data()
        # system_snapshot = SystemSnapshot(
        #     total_capacity=scheduling_data.total_capacity,
        #     user_allocations=scheduling_data.user_allocations,
        # )
        # workload = [SessionWorkload(...) for session in scheduling_data.pending_sessions]

        # Prioritize workloads with system context
        prioritized_workload = await self._prioritizer.prioritize(system_snapshot, workload)

        for session_workload in prioritized_workload:
            await self._schedule_session(session_workload)

    async def _schedule_session(self, workload: SessionWorkload) -> None:
        """
        Schedule a single session workload by validating it, applying the scheduling policy,
        and allocating resources.
        :param workload: The session workload to be scheduled.
        """
        self._validator.validate(workload)
        snapshot = AllocationSnapshot()
        self._allocator.allocate(workload, snapshot)
