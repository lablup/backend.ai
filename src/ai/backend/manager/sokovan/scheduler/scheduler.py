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
    KernelAllocation,
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
            try:
                if not session_workload.kernels:
                    log.warning(f"Session {session_workload.session_id} has no kernels")
                    continue

                # For single-node sessions, all kernels must have the same architecture
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

                # Convert to new criteria format
                criteria, selection_config = session_workload.to_agent_selection_criteria2(
                    max_container_count=config.max_container_count_per_agent,
                    enforce_spreading=config.enforce_spreading_endpoint_replica,
                )

                # Select agents for each kernel
                kernel_allocations: list[KernelAllocation] = []

                if session_workload.cluster_mode == ClusterMode.SINGLE_NODE:
                    # For single-node sessions, select one agent for all kernels
                    first_kernel = session_workload.kernels[0]
                    selected_agent_id = await self._agent_selector.select_agent_for_kernel(
                        agents_info,
                        criteria,
                        selection_config,
                        first_kernel.kernel_id,
                        session_workload.designated_agent,
                    )

                    if selected_agent_id:
                        # Find the selected agent info
                        selected_agent = next(
                            (agent for agent in agents_info if agent.agent_id == selected_agent_id),
                            None,
                        )
                        if selected_agent:
                            # Allocate all kernels to the same agent
                            for kernel in session_workload.kernels:
                                kernel_allocations.append(
                                    KernelAllocation(
                                        kernel_id=kernel.kernel_id,
                                        agent_id=selected_agent_id,
                                        agent_addr=selected_agent.agent_addr,
                                        scaling_group=selected_agent.scaling_group,
                                        requested_slots=kernel.requested_slots,
                                    )
                                )
                else:
                    # For multi-node sessions, select agents for each kernel independently
                    for kernel in session_workload.kernels:
                        selected_agent_id = await self._agent_selector.select_agent_for_kernel(
                            agents_info,
                            criteria,
                            selection_config,
                            kernel.kernel_id,
                            session_workload.designated_agent
                            if kernel == session_workload.kernels[0]
                            else None,
                        )

                        if selected_agent_id:
                            # Find the selected agent info
                            selected_agent = next(
                                (
                                    agent
                                    for agent in agents_info
                                    if agent.agent_id == selected_agent_id
                                ),
                                None,
                            )
                            if selected_agent:
                                kernel_allocations.append(
                                    KernelAllocation(
                                        kernel_id=kernel.kernel_id,
                                        agent_id=selected_agent_id,
                                        agent_addr=selected_agent.agent_addr,
                                        scaling_group=selected_agent.scaling_group,
                                        requested_slots=kernel.requested_slots,
                                    )
                                )

                # Create allocation snapshot if we have kernel allocations
                if kernel_allocations:
                    allocation_snapshot = AllocationSnapshot(
                        session_id=session_workload.session_id,
                        session_type=session_workload.session_type,
                        cluster_mode=session_workload.cluster_mode,
                        kernel_allocations=kernel_allocations,
                    )
                    allocations.append(allocation_snapshot)

            except Exception as e:
                log.debug(
                    "Agent selection failed for workload {}: {}",
                    session_workload.session_id,
                    e,
                )

        # Allocate resources for each validated workload
        await self._allocator.allocate(allocations)
