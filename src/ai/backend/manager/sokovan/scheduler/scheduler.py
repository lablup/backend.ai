import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Optional, Protocol

from ai.backend.common.types import ClusterMode
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.sokovan.scheduler.allocators.allocator import SchedulingAllocator
from ai.backend.manager.sokovan.scheduler.prioritizers.prioritizer import SchedulingPrioritizer
from ai.backend.manager.sokovan.scheduler.selectors.selector import AgentInfo, AgentSelector
from ai.backend.manager.sokovan.scheduler.types import (
    AllocationSnapshot,
    SessionWorkload,
    SystemSnapshot,
)
from ai.backend.manager.sokovan.scheduler.validators.validator import SchedulingValidator

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class SchedulingConfig:
    """Configuration needed for scheduling decisions."""

    max_container_count_per_agent: Optional[int]
    enforce_spreading_endpoint_replica: bool


class SchedulerRepository(Protocol):
    """Protocol for repository to fetch system state for scheduling."""

    async def get_system_snapshot(self) -> SystemSnapshot:
        """Get complete system snapshot for scheduling decisions."""
        ...

    async def get_agents(self) -> Sequence[AgentInfo]:
        """Get a list of available agents."""
        ...

    async def get_scheduling_config(self, scaling_group: str) -> SchedulingConfig:
        """Get scheduling configuration for a scaling group."""
        ...


@dataclass
class SchedulerArgs:
    validator: SchedulingValidator
    prioritizer: SchedulingPrioritizer
    agent_selector: AgentSelector
    allocator: SchedulingAllocator
    repository: SchedulerRepository


class Scheduler:
    _validator: SchedulingValidator
    _prioritizer: SchedulingPrioritizer
    _agent_selector: AgentSelector
    _allocator: SchedulingAllocator
    _repository: SchedulerRepository

    def __init__(self, args: SchedulerArgs) -> None:
        self._validator = args.validator
        self._prioritizer = args.prioritizer
        self._agent_selector = args.agent_selector
        self._allocator = args.allocator
        self._repository = args.repository

    async def enqueue(self, workload: SessionWorkload) -> None:
        """
        Enqueue a session workload for scheduling.
        This method should be called to add a new session workload to the scheduler's queue.
        """
        raise NotImplementedError("Enqueue method is not implemented yet.")

    async def _schedule_queued_sessions(self, workloads: Sequence[SessionWorkload]) -> None:
        """
        Schedule all queued sessions by prioritizing them and applying the scheduling policy.
        :param workload: A sequence of SessionWorkload objects to be scheduled.
        """
        # Fetch complete system snapshot from repository
        system_snapshot = await self._repository.get_system_snapshot()
        # Prioritize workloads with system context
        prioritized_workloads = await self._prioritizer.prioritize(system_snapshot, workloads)

        validates_workloads: list[SessionWorkload] = []
        for session_workload in prioritized_workloads:
            try:
                # Validate each workload against the current system state
                self._validator.validate(system_snapshot, session_workload)
                validates_workloads.append(session_workload)
            except Exception as e:
                log.debug(
                    "Validation failed for workload {}: {}",
                    session_workload.session_id,
                    e,
                )

        agents_info = await self._repository.get_agents()
        allocations: list[AllocationSnapshot] = []

        # Get scheduling configuration once for all workloads
        if not validates_workloads:
            return
        # Assuming all workloads in a batch are from the same scaling group
        first_workload = validates_workloads[0]
        config = await self._repository.get_scheduling_config(first_workload.scaling_group)

        for session_workload in validates_workloads:
            # TODO: Allocation Info should be received by the agent selector
            # current logic should be modified
            try:
                # For single-node sessions, all kernels must have the same architecture
                if not session_workload.kernels:
                    log.warning(f"Session {session_workload.session_id} has no kernels")
                    continue

                architectures = {kernel.architecture for kernel in session_workload.kernels}
                if (
                    session_workload.cluster_mode == ClusterMode.SINGLE_NODE
                    and len(architectures) > 1
                ):
                    log.error(
                        f"Single-node session {session_workload.session_id} has kernels with "
                        f"different architectures: {architectures}"
                    )
                    continue

                architecture = next(iter(architectures))  # Use any architecture for now

                criteria = session_workload.to_agent_selection_criteria(
                    architecture=architecture,
                    max_container_count=config.max_container_count_per_agent,
                    enforce_spreading=config.enforce_spreading_endpoint_replica,
                )

                allocation = self._agent_selector.select_agent(agents_info, criteria)
                if allocation is not None:
                    # TODO: AgentSelector Must return AllocationSnapshot instead of AgentId
                    allocations.append(allocation)  # type: ignore
            except Exception as e:
                log.debug(
                    "Agent selection failed for workload {}: {}",
                    session_workload.session_id,
                    e,
                )

        # Allocate resources for each validated workload
        await self._allocator.allocate(allocations)
