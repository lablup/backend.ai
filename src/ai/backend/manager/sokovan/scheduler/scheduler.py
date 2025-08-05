import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Protocol

from ai.backend.common.types import AgentId, AgentSelectionStrategy
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.sokovan.scheduler.prioritizers.prioritizer import SchedulingPrioritizer

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.allocators.allocator import SchedulingAllocator
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


@dataclass
class ScalingGroupInfo:
    """Scaling group configuration for scheduling."""

    scheduler_name: str
    agent_selection_strategy: AgentSelectionStrategy


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

    async def get_schedulable_scaling_groups(self) -> list[str]:
        """Get list of scaling groups with pending sessions."""
        ...

    async def get_pending_sessions(self, scaling_group: str) -> Sequence[SessionWorkload]:
        """Get pending sessions for a scaling group as workloads."""
        ...

    async def get_scaling_group_info(self, scaling_group: str) -> ScalingGroupInfo:
        """Get scaling group configuration including scheduler name and agent selection strategy."""
        ...


@dataclass
class SchedulerArgs:
    validator: SchedulingValidator
    prioritizer: SchedulingPrioritizer
    agent_selector: AgentSelector
    allocator: "SchedulingAllocator"
    repository: SchedulerRepository
    config_provider: ManagerConfigProvider


class Scheduler:
    _validator: SchedulingValidator
    _default_prioritizer: SchedulingPrioritizer
    _default_agent_selector: AgentSelector
    _allocator: "SchedulingAllocator"
    _repository: SchedulerRepository
    _config_provider: ManagerConfigProvider
    _prioritizer_pool: dict[str, SchedulingPrioritizer]
    _agent_selector_pool: dict[str, AgentSelector]

    def __init__(self, args: SchedulerArgs) -> None:
        self._validator = args.validator
        self._default_prioritizer = args.prioritizer
        self._default_agent_selector = args.agent_selector
        self._allocator = args.allocator
        self._repository = args.repository
        self._config_provider = args.config_provider
        self._prioritizer_pool = {}
        self._agent_selector_pool = {}

    def _get_prioritizer(self, scheduler_name: str) -> SchedulingPrioritizer:
        """Get prioritizer from pool or create new one."""
        if scheduler_name not in self._prioritizer_pool:
            # Import here to avoid circular imports
            if scheduler_name == "fifo":
                from ai.backend.manager.sokovan.scheduler.prioritizers.fifo import (
                    FIFOSchedulingPrioritizer,
                )

                self._prioritizer_pool[scheduler_name] = FIFOSchedulingPrioritizer()
            elif scheduler_name == "lifo":
                from ai.backend.manager.sokovan.scheduler.prioritizers.lifo import (
                    LIFOSchedulingPrioritizer,
                )

                self._prioritizer_pool[scheduler_name] = LIFOSchedulingPrioritizer()
            elif scheduler_name == "drf":
                from ai.backend.manager.sokovan.scheduler.prioritizers.drf import (
                    DRFSchedulingPrioritizer,
                )

                self._prioritizer_pool[scheduler_name] = DRFSchedulingPrioritizer()
            else:
                # Fallback to default
                self._prioritizer_pool[scheduler_name] = self._default_prioritizer
        return self._prioritizer_pool[scheduler_name]

    def _get_agent_selector(self, strategy: AgentSelectionStrategy) -> AgentSelector:
        """Get agent selector from pool or create new one."""
        strategy_name = strategy.value
        if strategy_name not in self._agent_selector_pool:
            # Get resource priority from config
            resource_priority = (
                self._config_provider.config.manager.agent_selection_resource_priority
            )

            # Import here to avoid circular imports
            if strategy == AgentSelectionStrategy.CONCENTRATED:
                from ai.backend.manager.sokovan.scheduler.selectors.concentrated import (
                    ConcentratedAgentSelector,
                )

                self._agent_selector_pool[strategy_name] = AgentSelector(
                    ConcentratedAgentSelector(resource_priority)
                )
            elif strategy == AgentSelectionStrategy.DISPERSED:
                from ai.backend.manager.sokovan.scheduler.selectors.dispersed import (
                    DispersedAgentSelector,
                )

                self._agent_selector_pool[strategy_name] = AgentSelector(
                    DispersedAgentSelector(resource_priority)
                )
            elif strategy == AgentSelectionStrategy.ROUNDROBIN:
                from ai.backend.manager.sokovan.scheduler.selectors.roundrobin import (
                    RoundRobinAgentSelector,
                )

                self._agent_selector_pool[strategy_name] = AgentSelector(RoundRobinAgentSelector())
            elif strategy == AgentSelectionStrategy.LEGACY:
                from ai.backend.manager.sokovan.scheduler.selectors.legacy import (
                    LegacyAgentSelector,
                )

                self._agent_selector_pool[strategy_name] = AgentSelector(
                    LegacyAgentSelector(resource_priority)
                )
            else:
                # Fallback to default
                self._agent_selector_pool[strategy_name] = self._default_agent_selector
        return self._agent_selector_pool[strategy_name]

    async def schedule_all_scaling_groups(self) -> bool:
        """
        Schedule sessions for all scaling groups.

        Returns:
            bool: True if any sessions were scheduled, False otherwise.
        """
        sessions_scheduled = False

        # Get all schedulable scaling groups from repository
        scaling_groups = await self._repository.get_schedulable_scaling_groups()

        for scaling_group in scaling_groups:
            try:
                # Get pending sessions for this scaling group as workloads
                workloads = await self._repository.get_pending_sessions(scaling_group)

                if not workloads:
                    continue

                # Schedule the workloads for this scaling group
                num_scheduled = await self._schedule_queued_sessions(scaling_group, workloads)

                if num_scheduled > 0:
                    sessions_scheduled = True

            except Exception as e:
                log.error(
                    "Failed to schedule sessions for scaling group {}: {}",
                    scaling_group,
                    str(e),
                    exc_info=True,
                )
                # Continue with other scaling groups even if one fails
                continue

        return sessions_scheduled

    async def _schedule_queued_sessions(
        self, scaling_group: str, workloads: Sequence[SessionWorkload]
    ) -> int:
        """
        Schedule all queued sessions by prioritizing them and applying the scheduling policy.

        :param scaling_group: The scaling group to schedule for
        :param workloads: A sequence of SessionWorkload objects to be scheduled
        :return: The number of sessions successfully scheduled
        """
        # Fetch complete system snapshot from repository
        system_snapshot = await self._repository.get_system_snapshot(scaling_group)
        config = await self._repository.get_scheduling_config(scaling_group)

        # Get scaling group specific configuration
        sg_info = await self._repository.get_scaling_group_info(scaling_group)

        # Get appropriate prioritizer for this scaling group
        prioritizer = self._get_prioritizer(sg_info.scheduler_name)

        # Prioritize workloads with system context
        prioritized_workloads = await prioritizer.prioritize(system_snapshot, workloads)

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
            return 0
        # Create selection config from scheduling config
        selection_config = AgentSelectionConfig(
            max_container_count=config.max_container_count_per_agent,
            enforce_spreading_endpoint_replica=config.enforce_spreading_endpoint_replica,
        )

        # Create a mutable copy of agents_info to track state changes during this scheduling session
        # This ensures concurrent scheduling sessions don't interfere with each other
        mutable_agents = list(agents_info)

        # Get appropriate agent selector for this scaling group
        agent_selector = self._get_agent_selector(sg_info.agent_selection_strategy)

        for session_workload in validates_workloads:
            session_allocation = await self._allocate_workload(
                session_workload,
                mutable_agents,
                selection_config,
                scaling_group,
                agent_selector,
            )
            if not session_allocation:
                continue
            session_allocations.append(session_allocation)

        # Allocate resources for each validated workload
        if session_allocations:
            await self._allocator.allocate(session_allocations)

        return len(session_allocations)

    async def _allocate_workload(
        self,
        session_workload: SessionWorkload,
        agents_info: Sequence[AgentInfo],
        selection_config: AgentSelectionConfig,
        scaling_group: str,
        agent_selector: AgentSelector,
    ) -> Optional[SessionAllocation]:
        """
        Allocate resources for a single session workload.

        :param session_workload: The workload to allocate
        :param agents_info: Available agents (will be modified with updated states)
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
                    selected_agent = await agent_selector.select_agent_for_resource_requirements(
                        agents_info,
                        resource_req,
                        criteria,
                        selection_config,
                        session_workload.designated_agent,
                    )

                    # Update the selected agent's state immediately for next selection
                    selected_agent.occupied_slots = (
                        selected_agent.occupied_slots + resource_req.requested_slots
                    )
                    selected_agent.container_count += len(resource_req.kernel_ids)

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

            # Create session allocation
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
                "Allocation failed for workload {}: {}",
                session_workload.session_id,
                e,
            )
            return None
