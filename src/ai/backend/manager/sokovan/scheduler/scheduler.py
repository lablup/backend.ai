import logging
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from ai.backend.common.types import AgentId, AgentSelectionStrategy
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.defs import LockID
from ai.backend.manager.metrics.scheduler import (
    SchedulerOperationMetricObserver,
    SchedulerPhaseMetricObserver,
)
from ai.backend.manager.types import DistributedLockFactory

from .selectors.concentrated import ConcentratedAgentSelector
from .selectors.dispersed import DispersedAgentSelector
from .selectors.exceptions import AgentSelectionError
from .selectors.legacy import LegacyAgentSelector
from .selectors.roundrobin import RoundRobinAgentSelector
from .selectors.selector import (
    AgentInfo,
    AgentSelectionConfig,
    AgentSelector,
)
from .sequencers.drf import DRFSequencer
from .sequencers.fifo import FIFOSequencer
from .sequencers.lifo import LIFOSequencer
from .sequencers.sequencer import WorkloadSequencer
from .types import (
    AgentAllocation,
    KernelAllocation,
    ScalingGroupInfo,
    SessionAllocation,
    SessionWorkload,
)
from .validators.validator import SchedulingValidator

if TYPE_CHECKING:
    from ai.backend.manager.repositories.schedule.repository import ScheduleRepository

    from .allocators.allocator import SchedulingAllocator

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class SchedulerArgs:
    validator: SchedulingValidator
    sequencer: WorkloadSequencer
    agent_selector: AgentSelector
    allocator: "SchedulingAllocator"
    repository: "ScheduleRepository"
    config_provider: ManagerConfigProvider
    lock_factory: DistributedLockFactory


class Scheduler:
    _validator: SchedulingValidator
    _default_sequencer: WorkloadSequencer
    _default_agent_selector: AgentSelector
    _allocator: "SchedulingAllocator"
    _repository: "ScheduleRepository"
    _config_provider: ManagerConfigProvider
    _lock_factory: DistributedLockFactory
    _sequencer_pool: Mapping[str, WorkloadSequencer]
    _agent_selector_pool: Mapping[AgentSelectionStrategy, AgentSelector]
    _operation_metrics: SchedulerOperationMetricObserver
    _phase_metrics: SchedulerPhaseMetricObserver

    def __init__(self, args: SchedulerArgs) -> None:
        self._validator = args.validator
        self._default_sequencer = args.sequencer
        self._default_agent_selector = args.agent_selector
        self._allocator = args.allocator
        self._repository = args.repository
        self._config_provider = args.config_provider
        self._lock_factory = args.lock_factory
        self._sequencer_pool = self._make_sequencer_pool()
        self._agent_selector_pool = self._make_agent_selector_pool(
            args.config_provider.config.manager.agent_selection_resource_priority
        )
        self._operation_metrics = SchedulerOperationMetricObserver.instance()
        self._phase_metrics = SchedulerPhaseMetricObserver.instance()

    @classmethod
    def _make_sequencer_pool(cls) -> Mapping[str, WorkloadSequencer]:
        """Initialize the sequencer pool with default sequencers."""
        pool: dict[str, WorkloadSequencer] = defaultdict(DRFSequencer)
        pool["fifo"] = FIFOSequencer()
        pool["lifo"] = LIFOSequencer()
        pool["drf"] = DRFSequencer()
        return pool

    @classmethod
    def _make_agent_selector_pool(
        cls, agent_selection_resource_priority: list[str]
    ) -> Mapping[AgentSelectionStrategy, AgentSelector]:
        """Initialize the agent selector pool with default selectors."""
        pool: dict[AgentSelectionStrategy, AgentSelector] = defaultdict(
            lambda: AgentSelector(ConcentratedAgentSelector(agent_selection_resource_priority))
        )
        pool[AgentSelectionStrategy.CONCENTRATED] = AgentSelector(
            ConcentratedAgentSelector(agent_selection_resource_priority)
        )
        pool[AgentSelectionStrategy.DISPERSED] = AgentSelector(
            DispersedAgentSelector(agent_selection_resource_priority)
        )
        pool[AgentSelectionStrategy.ROUNDROBIN] = AgentSelector(RoundRobinAgentSelector())
        pool[AgentSelectionStrategy.LEGACY] = AgentSelector(
            LegacyAgentSelector(agent_selection_resource_priority)
        )
        return pool

    async def schedule_all_scaling_groups(self) -> int:
        """
        Schedule sessions for all scaling groups.

        Returns:
            int: The number of sessions successfully scheduled.
        """
        lock_lifetime = self._config_provider.config.manager.session_schedule_lock_lifetime
        total_scheduled_count = 0
        # Acquire distributed lock before scheduling
        async with self._lock_factory(LockID.LOCKID_SCHEDULE, lock_lifetime):
            async with self._operation_metrics.measure_operation("schedule_all_scaling_groups"):
                # Get all schedulable scaling groups from repository
                scaling_groups = await self._repository.get_schedulable_scaling_groups()
                for scaling_group in scaling_groups:
                    try:
                        log.info("Scheduling sessions for scaling group: {}", scaling_group)
                        # Schedule sessions for this scaling group
                        async with self._operation_metrics.measure_operation(
                            "schedule_scaling_group",
                        ):
                            scheduled_count = await self._schedule_scaling_group(scaling_group)
                        total_scheduled_count += scheduled_count
                        if scheduled_count > 0:
                            log.info(
                                "Scheduled {} sessions for scaling group: {}",
                                scheduled_count,
                                scaling_group,
                            )
                    except Exception as e:
                        log.error(
                            "Failed to schedule sessions for scaling group {}: {}",
                            scaling_group,
                            str(e),
                            exc_info=True,
                        )
                        # Continue with other scaling groups even if one fails
                        continue

                return total_scheduled_count

    async def _schedule_scaling_group(self, scaling_group: str) -> int:
        """
        Schedule sessions for a specific scaling group.
        Args:
            scaling_group: The scaling group to schedule for.
        Returns:
            int: The number of sessions successfully scheduled.
        """
        # Get scaling group specific configuration first
        # TODO: 아래 두개의 메소드는 합쳐져야 함
        # 내부적으로 private method를 db_session을 사용하여 호출하도록 변경
        sg_info = await self._repository.get_scaling_group_info_for_sokovan(scaling_group)
        # Get pending sessions for this scaling group as workloads
        workloads = await self._repository.get_pending_sessions(
            scaling_group, sg_info.pending_timeout
        )
        if not workloads:
            log.info(
                "No pending sessions for scaling group {}. Skipping scheduling.",
                scaling_group,
            )
            return 0

        # Schedule the workloads for this scaling group
        return await self._schedule_queued_sessions(scaling_group, workloads, sg_info)

    async def _schedule_queued_sessions(
        self, scaling_group: str, workloads: Sequence[SessionWorkload], sg_info: ScalingGroupInfo
    ) -> int:
        """
        Schedule all queued sessions by sequencing them and applying the scheduling policy.

        :param scaling_group: The scaling group to schedule for
        :param workloads: A sequence of SessionWorkload objects to be scheduled
        :return: The number of sessions successfully scheduled
        """
        # No need to record queued sessions here, they are recorded during scheduling phases

        # Fetch complete system snapshot from repository
        async with self._phase_metrics.measure_phase(scaling_group, "system_snapshot"):
            # Get the current system snapshot and scheduling configuration
            # TODO: 2개 요청을 합쳐서 하나의 public method로 변경
            # 다만 2개 동작이 다르니 private method로 변경하여 db_session을 사용하도록 함
            system_snapshot = await self._repository.get_system_snapshot(scaling_group)
            config = await self._repository.get_scheduling_config(scaling_group)
            selection_config = AgentSelectionConfig(
                max_container_count=config.max_container_count_per_agent,
                enforce_spreading_endpoint_replica=config.enforce_spreading_endpoint_replica,
            )

        # Validation phase with timing
        async with self._phase_metrics.measure_phase(scaling_group, "validation"):
            validated_workloads: list[SessionWorkload] = []
            for session_workload in workloads:
                try:
                    # Validate each workload against the current system state
                    self._validator.validate(system_snapshot, session_workload)
                    validated_workloads.append(session_workload)
                except Exception as e:
                    log.info(
                        "Validation failed for workload {}: {}",
                        session_workload.session_id,
                        e,
                    )
                    # Validation failure is already recorded by context manager

        # Get scheduling configuration once for all workloads
        if not validated_workloads:
            log.info(
                "No valid workloads to schedule for scaling group {}. Skipping scheduling.",
                scaling_group,
            )
            return 0

        # Sequence workloads with system context
        async with self._phase_metrics.measure_phase(
            scaling_group, f"sequencing_{sg_info.scheduler_name}"
        ):
            sequencer = self._sequencer_pool[sg_info.scheduler_name]
            sequenced_workloads = await sequencer.sequence(system_snapshot, validated_workloads)

        mutable_agents = await self._repository.get_agents(scaling_group)
        session_allocations: list[SessionAllocation] = []
        # Get appropriate agent selector for this scaling group
        agent_selector = self._agent_selector_pool[sg_info.agent_selection_strategy]
        async with self._phase_metrics.measure_phase(scaling_group, "allocation"):
            for session_workload in sequenced_workloads:
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
                log.info(
                    "Allocating resources for {} session allocations in scaling group {}",
                    len(session_allocations),
                    scaling_group,
                )
                await self._allocator.allocate(session_allocations)

        # Allocation metrics are recorded in _allocate_workload

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
                    # Agent selection is part of allocation phase

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
                # Allocation failure is already recorded by context manager
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
            # Allocation failure is already recorded by context manager
            return None
