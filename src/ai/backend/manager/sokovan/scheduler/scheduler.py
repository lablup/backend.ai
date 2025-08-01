from collections.abc import Sequence
from dataclasses import dataclass

from ai.backend.manager.sokovan.scheduler.allocators.allocator import (
    AllocationSnapshot,
    ResourceAllocator,
)
from ai.backend.manager.sokovan.scheduler.prioritizers.prioritizer import SchedulingPrioritizer
from ai.backend.manager.sokovan.scheduler.validators.validator import (
    SchedulingValidator,
    SessionWorkload,
)


@dataclass
class SchedulerArgs:
    validator: SchedulingValidator
    allocator: ResourceAllocator
    prioritizer: SchedulingPrioritizer


class Scheduler:
    _prioritizer: SchedulingPrioritizer
    _validator: SchedulingValidator
    _allocator: ResourceAllocator

    def __init__(self, args: SchedulerArgs) -> None:
        self._prioritizer = args.prioritizer
        self._validator = args.validator
        self._allocator = args.allocator

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
        prioritized_workload = await self._prioritizer.prioritize(workload)
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
