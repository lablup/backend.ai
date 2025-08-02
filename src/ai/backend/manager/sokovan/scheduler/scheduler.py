from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from ai.backend.manager.sokovan.scheduler.allocators.allocator import (
    AllocationSnapshot,
    ResourceAllocator,
)
from ai.backend.manager.sokovan.scheduler.prioritizers.prioritizer import SchedulingPrioritizer
from ai.backend.manager.sokovan.scheduler.types import SessionWorkload, SystemSnapshot
from ai.backend.manager.sokovan.scheduler.validators.validator import SchedulingValidator


class SchedulerRepository(Protocol):
    """Protocol for repository to fetch system state for scheduling."""

    async def get_system_snapshot(self) -> SystemSnapshot:
        """Get complete system snapshot for scheduling decisions."""
        ...


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
        # Fetch complete system snapshot from repository
        system_snapshot = await self._repository.get_system_snapshot()

        # Prioritize workloads with system context
        prioritized_workload = await self._prioritizer.prioritize(system_snapshot, workload)

        for session_workload in prioritized_workload:
            await self._schedule_session(system_snapshot, session_workload)

    async def _schedule_session(
        self, system_snapshot: SystemSnapshot, workload: SessionWorkload
    ) -> None:
        """
        Schedule a single session workload by validating it, applying the scheduling policy,
        and allocating resources.
        :param system_snapshot: The current system state snapshot.
        :param workload: The session workload to be scheduled.
        """
        self._validator.validate(system_snapshot, workload)
        allocation_snapshot = AllocationSnapshot()
        self._allocator.allocate(workload, allocation_snapshot)
