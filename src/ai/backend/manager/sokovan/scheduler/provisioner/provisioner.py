from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.types import (
    AgentSelectionStrategy,
    ResourceSlot,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.metrics.scheduler import (
    SchedulerPhaseMetricObserver,
)
from ai.backend.manager.repositories.scheduler import (
    SchedulerRepository,
    SchedulingData,
)

from ..results import ScheduleResult
from ..types import (
    AllocationBatch,
    KeypairOccupancy,
    SchedulingConfig,
    SchedulingFailure,
    SchedulingPredicate,
    SessionAllocation,
    SessionWorkload,
    SystemSnapshot,
)
from .allocators.allocator import SchedulingAllocator
from .selectors.concentrated import ConcentratedAgentSelector
from .selectors.dispersed import DispersedAgentSelector
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
from .sequencers.sequencer import SchedulingSequencer, WorkloadSequencer
from .validators.validator import SchedulingValidator

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class SessionProvisionerArgs:
    validator: SchedulingValidator
    default_sequencer: WorkloadSequencer
    default_agent_selector: AgentSelector
    allocator: SchedulingAllocator
    repository: SchedulerRepository
    config_provider: ManagerConfigProvider
    valkey_schedule: ValkeyScheduleClient


class SessionProvisioner:
    """
    Handles the PENDING -> SCHEDULED transition for sessions.

    Orchestrates the provisioning pipeline:
    1. Validation (via validators)
    2. Sequencing (via sequencers)
    3. Agent selection (via selectors)
    4. Resource allocation (via allocators)
    """

    _validator: SchedulingValidator
    _default_sequencer: WorkloadSequencer
    _default_agent_selector: AgentSelector
    _allocator: SchedulingAllocator
    _repository: SchedulerRepository
    _config_provider: ManagerConfigProvider
    _sequencer_pool: Mapping[str, WorkloadSequencer]
    _agent_selector_pool: Mapping[AgentSelectionStrategy, AgentSelector]
    _phase_metrics: SchedulerPhaseMetricObserver
    _valkey_schedule: ValkeyScheduleClient

    def __init__(self, args: SessionProvisionerArgs) -> None:
        self._validator = args.validator
        self._default_sequencer = args.default_sequencer
        self._default_agent_selector = args.default_agent_selector
        self._allocator = args.allocator
        self._repository = args.repository
        self._config_provider = args.config_provider
        self._valkey_schedule = args.valkey_schedule
        self._sequencer_pool = self._make_sequencer_pool()
        self._agent_selector_pool = self._make_agent_selector_pool(
            args.config_provider.config.manager.agent_selection_resource_priority
        )
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

    def _get_sequencer(self, name: str) -> SchedulingSequencer:
        sequncer = self._sequencer_pool[name]
        return SchedulingSequencer(sequncer)

    async def schedule_scaling_group(self, scaling_group: str) -> ScheduleResult:
        """
        Schedule sessions for a specific scaling group.
        Args:
            scaling_group: The scaling group to schedule for.
        Returns:
            ScheduleResult containing count and session data
        """
        # Single optimized call to get all scheduling data
        # This consolidates: get_scaling_group_info_for_sokovan, get_pending_sessions,
        # get_system_snapshot, and get_scheduling_config into ONE DB session
        scheduling_data = await self._repository.get_scheduling_data(scaling_group)

        if scheduling_data is None:
            log.trace(
                "No pending sessions for scaling group {}. Skipping scheduling.",
                scaling_group,
            )
            return ScheduleResult()

        # Schedule using the scheduling data - no more DB calls needed
        return await self._schedule_queued_sessions_with_data(scaling_group, scheduling_data)

    async def _schedule_queued_sessions_with_data(
        self, scaling_group: str, scheduling_data: SchedulingData
    ) -> ScheduleResult:
        """
        Schedule all queued sessions using pre-fetched scheduling data.
        No database calls are made in this method - all data comes from scheduling_data.

        :param scaling_group: The scaling group to schedule for
        :param scheduling_data: Pre-fetched data containing all necessary information
        :return: The number of sessions successfully scheduled
        """
        # Use data from scheduling_data instead of making DB calls
        # Convert PendingSessionData to SessionWorkload
        workloads = [
            session.to_session_workload() for session in scheduling_data.pending_sessions.sessions
        ]
        sg_info = scheduling_data.scaling_group

        if not scheduling_data.snapshot_data:
            log.warning("Missing snapshot data for scaling group {}", scaling_group)
            return ScheduleResult()

        # Convert snapshot data to SystemSnapshot
        system_snapshot = scheduling_data.snapshot_data.to_system_snapshot(
            scheduling_data.spec.known_slot_types, scheduling_data.total_capacity
        )

        # Create scheduling config from spec and scaling group opts
        config = SchedulingConfig(
            max_container_count_per_agent=scheduling_data.spec.max_container_count,
            enforce_spreading_endpoint_replica=sg_info.scheduler_opts.enforce_spreading_endpoint_replica,
        )

        selection_config = AgentSelectionConfig(
            max_container_count=config.max_container_count_per_agent,
            enforce_spreading_endpoint_replica=config.enforce_spreading_endpoint_replica,
        )
        # Add sequencing predicate to track in passed predicates
        with self._phase_metrics.measure_phase(
            "scheduler", scaling_group, f"sequencing_{sg_info.scheduler}"
        ):
            sequencer = self._get_sequencer(sg_info.scheduler)
            sequenced_workloads = sequencer.sequence(system_snapshot, workloads)

        # Build mutable agents with occupancy data from snapshot
        agent_occupancy = (
            scheduling_data.snapshot_data.resource_occupancy.by_agent
            if scheduling_data.snapshot_data
            else {}
        )
        mutable_agents = [
            AgentInfo(
                agent_id=agent.id,
                agent_addr=agent.addr,
                architecture=agent.architecture,
                scaling_group=agent.scaling_group,
                available_slots=agent.available_slots,
                occupied_slots=(
                    agent_occupancy[agent.id].occupied_slots
                    if agent.id in agent_occupancy
                    else ResourceSlot()
                ),
                container_count=(
                    agent_occupancy[agent.id].container_count if agent.id in agent_occupancy else 0
                ),
            )
            for agent in scheduling_data.agents
        ]
        session_allocations: list[SessionAllocation] = []
        scheduling_failures: list[SchedulingFailure] = []
        # Get agent selection strategy from scheduler opts config
        agent_selection_strategy = sg_info.scheduler_opts.agent_selection_strategy
        agent_selector = self._agent_selector_pool[agent_selection_strategy]
        for session_workload in sequenced_workloads:
            # Track predicates for this session
            passed_phases: list[SchedulingPredicate] = []
            failed_phases: list[SchedulingPredicate] = []
            passed_phases.append(
                SchedulingPredicate(name=sequencer.name, msg=sequencer.success_message())
            )

            try:
                session_allocation = await self._schedule_workload(
                    scaling_group,
                    system_snapshot,
                    mutable_agents,
                    selection_config,
                    agent_selector,
                    session_workload,
                    passed_phases,
                    failed_phases,
                )
                session_allocations.append(session_allocation)
            except Exception as e:
                log.debug(
                    "Scheduling failed for workload {}: {}",
                    session_workload.session_id,
                    e,
                )
                if not failed_phases:
                    # If no specific failure predicates were added, add a exception information
                    failed_phases.append(
                        SchedulingPredicate(
                            name=type(e).__name__,
                            msg=str(e),
                        )
                    )

                failure = SchedulingFailure(
                    session_id=session_workload.session_id,
                    passed_phases=passed_phases,
                    failed_phases=failed_phases,
                    msg=str(e),
                )
                scheduling_failures.append(failure)
                continue
        log.info(
            "Processing {} allocations and {} failures in scaling group {}",
            len(session_allocations),
            len(scheduling_failures),
            scaling_group,
        )
        # Create batch with allocations and failures
        batch = AllocationBatch(
            allocations=session_allocations,
            failures=scheduling_failures,
        )
        with self._phase_metrics.measure_phase("scheduler", scaling_group, "allocation"):
            scheduled_sessions = await self._allocator.allocate(batch)

        failure_ids = [f.session_id for f in scheduling_failures]
        await self._valkey_schedule.set_pending_queue(scaling_group, failure_ids)
        return ScheduleResult(
            scheduled_sessions=scheduled_sessions,
        )

    async def _schedule_workload(
        self,
        scaling_group: str,
        mutable_snapshot: SystemSnapshot,
        mutable_agents: Sequence[AgentInfo],
        selection_config: AgentSelectionConfig,
        agent_selector: AgentSelector,
        session_workload: SessionWorkload,
        passed_phases: list[SchedulingPredicate],
        failed_phases: list[SchedulingPredicate],
    ) -> SessionAllocation:
        # Phase 1: Validation
        with self._phase_metrics.measure_phase("scheduler", scaling_group, "validation"):
            # validate_with_predicates will update both lists and raise if validation fails
            self._validator.validate(
                mutable_snapshot, session_workload, passed_phases, failed_phases
            )

        # Phase 2: Agent Selection
        with self._phase_metrics.measure_phase("scheduler", scaling_group, "agent_selection"):
            try:
                session_allocation = await self._allocate_workload(
                    session_workload,
                    mutable_agents,
                    selection_config,
                    scaling_group,
                    agent_selector,
                )
                # Agent selection succeeded - add to passed predicates
                passed_phases.append(
                    SchedulingPredicate(
                        name=agent_selector.strategy_name(),
                        msg=agent_selector.strategy_success_message(),
                    )
                )
            except Exception as e:
                # Add failed predicate for agent selection
                failed_phases.append(
                    SchedulingPredicate(name=agent_selector.strategy_name(), msg=str(e))
                )
                raise

        # Phase 3: Allocation success - add allocator predicate
        passed_phases.append(
            SchedulingPredicate(name=self._allocator.name(), msg=self._allocator.success_message())
        )

        # Update the snapshot to reflect this allocation
        # Note: agent state changes are already applied to mutable_agents by select_agents_for_batch_requirements
        self._update_system_snapshot(
            mutable_snapshot,
            session_workload,
            session_allocation,
        )

        # Store predicates in the allocation
        session_allocation.passed_phases = passed_phases
        session_allocation.failed_phases = failed_phases
        return session_allocation

    def _update_system_snapshot(
        self,
        snapshot: SystemSnapshot,
        workload: SessionWorkload,
        allocation: SessionAllocation,
    ) -> None:
        """
        Update the system snapshot after a session allocation.
        This ensures the next validation uses up-to-date information.

        :param snapshot: The system snapshot to update (modified in-place)
        :param workload: The session workload that was allocated
        :param allocation: The session allocation result containing agent allocations
        """
        # Calculate total allocated resources from allocation
        total_allocated_slots = ResourceSlot()
        for agent_alloc in allocation.agent_allocations:
            for slot in agent_alloc.allocated_slots:
                total_allocated_slots += slot

        # 1. Update resource occupancy - add the session's allocated slots
        # Update keypair occupancy
        current_keypair = snapshot.resource_occupancy.by_keypair.get(workload.access_key)
        if current_keypair is None:
            current_keypair = KeypairOccupancy(
                occupied_slots=ResourceSlot(), session_count=0, sftp_session_count=0
            )

        # Update occupied slots and session counts
        current_keypair.occupied_slots += total_allocated_slots
        if workload.is_private:
            current_keypair.sftp_session_count += 1
        else:
            current_keypair.session_count += 1

        snapshot.resource_occupancy.by_keypair[workload.access_key] = current_keypair

        # Update user occupancy
        current_user = snapshot.resource_occupancy.by_user.get(workload.user_uuid, ResourceSlot())
        snapshot.resource_occupancy.by_user[workload.user_uuid] = (
            current_user + total_allocated_slots
        )

        # Update group occupancy
        current_group = snapshot.resource_occupancy.by_group.get(workload.group_id, ResourceSlot())
        snapshot.resource_occupancy.by_group[workload.group_id] = (
            current_group + total_allocated_slots
        )

        # Update domain occupancy
        current_domain = snapshot.resource_occupancy.by_domain.get(
            workload.domain_name, ResourceSlot()
        )
        snapshot.resource_occupancy.by_domain[workload.domain_name] = (
            current_domain + total_allocated_slots
        )

        # 2. Update concurrency counts
        if workload.is_private:
            # Increment SFTP session count
            current_sftp = snapshot.concurrency.sftp_sessions_by_keypair.get(workload.access_key, 0)
            snapshot.concurrency.sftp_sessions_by_keypair[workload.access_key] = current_sftp + 1
        else:
            # Increment regular session count
            current_sessions = snapshot.concurrency.sessions_by_keypair.get(workload.access_key, 0)
            snapshot.concurrency.sessions_by_keypair[workload.access_key] = current_sessions + 1

    async def _allocate_workload(
        self,
        session_workload: SessionWorkload,
        agents_info: Sequence[AgentInfo],
        selection_config: AgentSelectionConfig,
        scaling_group: str,
        agent_selector: AgentSelector,
    ) -> SessionAllocation:
        """
        Allocate resources for a single session workload.

        :param session_workload: The workload to allocate
        :param agents_info: Available agents (will be modified with updated states)
        :param selection_config: Agent selection configuration
        :param scaling_group: The scaling group name
        :return: SessionAllocation
        :raises AgentSelectionError: If agent selection fails
        """
        # Convert to new criteria format
        criteria = session_workload.to_agent_selection_criteria()

        # Use batch selection method - it will get resource requirements internally
        # and apply state changes to agents_info
        selections = await agent_selector.select_agents_for_batch_requirements(
            agents_info,
            criteria,
            selection_config,
            session_workload.designated_agent_ids,
        )

        # Build session allocation from selections
        return SessionAllocation.from_agent_selections(
            session_workload,
            selections,
            scaling_group,
        )
