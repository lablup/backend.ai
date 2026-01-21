from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.types import (
    AgentSelectionStrategy,
    ResourceSlot,
    SessionId,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.metrics.scheduler import (
    SchedulerPhaseMetricObserver,
)
from ai.backend.manager.repositories.fair_share import FairShareRepository
from ai.backend.manager.repositories.scheduler import (
    SchedulerRepository,
    SchedulingData,
)
from ai.backend.manager.sokovan.recorder import (
    ExecutionRecord,
    RecorderContext,
    StepStatus,
)
from ai.backend.manager.sokovan.scheduler.results import ScheduleResult
from ai.backend.manager.sokovan.scheduler.types import (
    AllocationBatch,
    KeypairOccupancy,
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
from .sequencers.fair_share import FairShareSequencer
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
    fair_share_repository: FairShareRepository
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
    _fair_share_repository: FairShareRepository
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
        self._fair_share_repository = args.fair_share_repository
        self._config_provider = args.config_provider
        self._valkey_schedule = args.valkey_schedule
        self._sequencer_pool = self._make_sequencer_pool()
        self._agent_selector_pool = self._make_agent_selector_pool(
            args.config_provider.config.manager.agent_selection_resource_priority
        )
        self._phase_metrics = SchedulerPhaseMetricObserver.instance()

    def _make_sequencer_pool(self) -> Mapping[str, WorkloadSequencer]:
        """Initialize the sequencer pool with default sequencers."""
        pool: dict[str, WorkloadSequencer] = defaultdict(DRFSequencer)
        pool["fifo"] = FIFOSequencer()
        pool["lifo"] = LIFOSequencer()
        pool["drf"] = DRFSequencer()
        pool["fairshare"] = FairShareSequencer(self._fair_share_repository)
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

    async def schedule_scaling_group(
        self,
        scaling_group: str,
        scheduling_data: SchedulingData,
    ) -> ScheduleResult:
        """
        Schedule sessions for a specific scaling group.

        This method orchestrates the full provisioning pipeline using pre-fetched data:
        1. Sequencing: Order workloads using configured sequencer (FIFO/LIFO/DRF)
        2. Validation: Check quotas and constraints for each workload
        3. Agent selection: Select agents using configured strategy
        4. Allocation: Persist allocations to database

        Args:
            scaling_group: The scaling group to schedule for.
            scheduling_data: Pre-fetched scheduling data from Handler.

        Returns:
            ScheduleResult containing scheduled session data
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

        # Create agent selection config directly from spec and scaling group opts
        selection_config = AgentSelectionConfig(
            max_container_count=scheduling_data.spec.max_container_count,
            enforce_spreading_endpoint_replica=sg_info.scheduler_opts.enforce_spreading_endpoint_replica,
        )
        # Perform sequencing (batch operation for all workloads)
        # Record as shared phase so all entity records include it
        sequencer = self._get_sequencer(sg_info.scheduler)
        with (
            self._phase_metrics.measure_phase(
                "scheduler", scaling_group, f"sequencing_{sg_info.scheduler}"
            ),
            RecorderContext[SessionId].shared_phase(
                "sequencing", success_detail=sequencer.success_message()
            ),
            RecorderContext[SessionId].shared_step(
                sequencer.name, success_detail=sequencer.success_message()
            ),
        ):
            sequenced_workloads = await sequencer.sequence(
                scaling_group, system_snapshot, workloads
            )

        # Build mutable agents with occupancy data from snapshot
        agent_occupancy = (
            scheduling_data.snapshot_data.resource_occupancy.by_agent
            if scheduling_data.snapshot_data
            else {}
        )
        mutable_agents = [
            AgentInfo.from_meta_and_occupancy(agent, agent_occupancy)
            for agent in scheduling_data.agents
        ]
        session_allocations: list[SessionAllocation] = []
        scheduling_failures: list[SchedulingFailure] = []
        # Get agent selection strategy from scheduler opts config
        agent_selection_strategy = sg_info.scheduler_opts.agent_selection_strategy
        agent_selector = self._agent_selector_pool[agent_selection_strategy]

        # Get current pool from RecorderContext (scope opened by coordinator)
        pool = RecorderContext[SessionId].current_pool()

        for session_workload in sequenced_workloads:
            try:
                # Sequencing phase is automatically included via shared phases
                session_allocation = await self._schedule_workload(
                    scaling_group,
                    system_snapshot,
                    mutable_agents,
                    selection_config,
                    agent_selector,
                    session_workload,
                )
                session_allocations.append(session_allocation)
            except Exception as e:
                log.debug(
                    "Scheduling failed for workload {}: {}",
                    session_workload.session_id,
                    e,
                )
                # Get execution record from pool and convert to SchedulingFailure
                record = pool.get_record(session_workload.session_id)
                passed, failed = self._convert_record_to_predicates(record)
                failure = SchedulingFailure(
                    session_id=session_workload.session_id,
                    passed_phases=passed,
                    failed_phases=failed,
                    msg=str(e),
                )
                scheduling_failures.append(failure)
                continue

        # Convert execution records to passed_phases/failed_phases for allocations
        for allocation in session_allocations:
            record = pool.get_record(allocation.session_id)
            if record:
                passed, failed = self._convert_record_to_predicates(record)
                allocation.passed_phases = passed
                allocation.failed_phases = failed

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
    ) -> SessionAllocation:
        pool = RecorderContext[SessionId].current_pool()
        recorder = pool.recorder(session_workload.session_id)

        # Phase 1: Validation
        with self._phase_metrics.measure_phase("scheduler", scaling_group, "validation"):
            with recorder.phase("validation"):
                self._validator.validate(mutable_snapshot, session_workload)

        # Phase 2: Agent Selection
        with self._phase_metrics.measure_phase("scheduler", scaling_group, "agent_selection"):
            with recorder.phase(
                "agent_selection", success_detail=agent_selector.strategy_success_message()
            ):
                with recorder.step(
                    agent_selector.strategy_name(),
                    success_detail=agent_selector.strategy_success_message(),
                ):
                    session_allocation = await self._allocate_workload(
                        session_workload,
                        mutable_agents,
                        selection_config,
                        scaling_group,
                        agent_selector,
                    )

        # Phase 3: Allocation (prepare)
        with recorder.phase("allocation", success_detail=self._allocator.success_message()):
            with recorder.step(
                self._allocator.name(), success_detail=self._allocator.success_message()
            ):
                # Update the snapshot to reflect this allocation
                # Note: agent state changes are already applied to mutable_agents
                self._update_system_snapshot(
                    mutable_snapshot,
                    session_workload,
                    session_allocation,
                )

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

    @staticmethod
    def _convert_record_to_predicates(
        record: ExecutionRecord | None,
    ) -> tuple[list[SchedulingPredicate], list[SchedulingPredicate]]:
        """
        Convert an ExecutionRecord to passed/failed SchedulingPredicate lists.

        Args:
            record: The execution record to convert (may be None if entity context failed early)

        Returns:
            Tuple of (passed_predicates, failed_predicates)
        """
        passed: list[SchedulingPredicate] = []
        failed: list[SchedulingPredicate] = []

        if record is None:
            return passed, failed

        for phase in record.phases:
            # Add phase-level predicate
            phase_predicate = SchedulingPredicate(
                name=phase.name,
                msg=phase.detail or "",
            )
            if phase.status == StepStatus.SUCCESS:
                passed.append(phase_predicate)
            else:
                failed.append(phase_predicate)

            # Add step-level predicates
            for step in phase.steps:
                step_predicate = SchedulingPredicate(
                    name=step.name,
                    msg=step.detail or "",
                )
                if step.status == StepStatus.SUCCESS:
                    passed.append(step_predicate)
                else:
                    failed.append(step_predicate)

        return passed, failed
