import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Optional, Protocol

from ai.backend.common.types import AgentId
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.sokovan.scheduler.allocators.allocator import SchedulingAllocator
from ai.backend.manager.sokovan.scheduler.prioritizers.prioritizer import SchedulingPrioritizer
from ai.backend.manager.sokovan.scheduler.selectors.exceptions import AgentSelectionError
from ai.backend.manager.sokovan.scheduler.selectors.selector import (
    AgentInfo,
    AgentSelectionConfig,
    AgentSelector,
)
from ai.backend.manager.sokovan.scheduler.types import (
    AgentAllocation,
    KernelAllocation,
    SessionAllocation,
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

    async def get_system_snapshot(self, scaling_group: str) -> SystemSnapshot:
        """Get complete system snapshot for scheduling decisions."""
        ...

    async def get_agents(self, scaling_group: str) -> Sequence[AgentInfo]:
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

    async def _schedule_queued_sessions(
        self, scaling_group: str, workloads: Sequence[SessionWorkload]
    ) -> None:
        """
        Schedule all queued sessions by prioritizing them and applying the scheduling policy.
        :param workload: A sequence of SessionWorkload objects to be scheduled.
        """
        # Fetch complete system snapshot from repository
        system_snapshot = await self._repository.get_system_snapshot(scaling_group)
        config = await self._repository.get_scheduling_config(scaling_group)
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

        agents_info = await self._repository.get_agents(scaling_group)
        session_allocations: list[SessionAllocation] = []

        # Get scheduling configuration once for all workloads
        if not validates_workloads:
            return
        # Create selection config from scheduling config
        selection_config = AgentSelectionConfig(
            max_container_count=config.max_container_count_per_agent,
            enforce_spreading_endpoint_replica=config.enforce_spreading_endpoint_replica,
        )
        for session_workload in validates_workloads:
            session_allocation = await self._allocate_workload(
                session_workload,
                agents_info,
                selection_config,
                scaling_group,
            )
            if not session_allocation:
                continue
            session_allocations.append(session_allocation)

        # Allocate resources for each validated workload
        await self._allocator.allocate(session_allocations)

    async def _allocate_workload(
        self,
        session_workload: SessionWorkload,
        agents_info: Sequence[AgentInfo],
        selection_config: AgentSelectionConfig,
        scaling_group: str,
    ) -> Optional[SessionAllocation]:
        """
        Allocate resources for a single session workload.

        :param session_workload: The workload to allocate
        :param agents_info: Available agents
        :param selection_config: Agent selection configuration
        :param scaling_group: The scaling group name
        :return: SessionAllocation if successful, None otherwise
        """
        try:
            # Convert to new criteria format
            criteria = session_workload.to_agent_selection_criteria()

            # Get resource requirements based on cluster mode
            resource_requirements = criteria.get_resource_requirements()
            if not resource_requirements:
                log.debug(
                    "No resource requirements found for session {}",
                    session_workload.session_id,
                )
                return None

            kernel_allocations: list[KernelAllocation] = []
            # Track agent allocations: agent_id -> AgentAllocation
            agent_allocation_map: dict[AgentId, AgentAllocation] = {}

            try:
                # Process each resource requirement
                for resource_req in resource_requirements:
                    # Only apply designated agent to the first selection
                    selected_agent = (
                        await self._agent_selector.select_agent_for_resource_requirements(
                            agents_info,
                            resource_req,
                            criteria,
                            selection_config,
                            session_workload.designated_agent,
                        )
                    )

                    # Track resource allocation for this agent
                    if selected_agent.agent_id not in agent_allocation_map:
                        agent_allocation_map[selected_agent.agent_id] = AgentAllocation(
                            agent_id=selected_agent.agent_id,
                            allocated_slots=[],
                        )
                    agent_allocation_map[selected_agent.agent_id].allocated_slots.append(
                        resource_req.requested_slots
                    )

                    # Create kernel allocations
                    for kernel_id in resource_req.kernel_ids:
                        kernel_allocations.append(
                            KernelAllocation(
                                kernel_id=kernel_id,
                                agent_id=selected_agent.agent_id,
                                agent_addr=selected_agent.agent_addr,
                                scaling_group=selected_agent.scaling_group,
                            )
                        )

            except AgentSelectionError as e:
                log.debug(
                    "Agent selection failed for session {}: {}",
                    session_workload.session_id,
                    e,
                )
                return None

            # Create session allocation if we have kernel allocations
            if kernel_allocations:
                # If no agent allocations, we cannot proceed
                return None
            # Get agent allocations from the map
            agent_allocations = list(agent_allocation_map.values())

            return SessionAllocation(
                session_id=session_workload.session_id,
                session_type=session_workload.session_type,
                cluster_mode=session_workload.cluster_mode,
                scaling_group=scaling_group,
                kernel_allocations=kernel_allocations,
                agent_allocations=agent_allocations,
            )
        except Exception as e:
            log.debug(
                "Agent selection failed for workload {}: {}",
                session_workload.session_id,
                e,
            )
            return None
