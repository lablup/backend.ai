from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.identifier.resource_group import ResourceGroupName
from ai.backend.common.types import (
    AgentId,
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
from ai.backend.manager.repositories.scheduler import SchedulerRepository
from ai.backend.manager.sokovan.recorder import (
    ExecutionRecord,
    RecorderContext,
    StepStatus,
)
from ai.backend.manager.sokovan.scheduler.results import ScheduleResult
from ai.backend.manager.views.sokovan.allocation import (
    AgentAllocation,
    AllocationBatch,
    KernelAllocation,
    SchedulingFailure,
    SchedulingPredicate,
    SessionAllocation,
)
from ai.backend.manager.views.sokovan.resource_group import ResourceGroupMeta
from ai.backend.manager.views.sokovan.scheduling import SchedulingData
from ai.backend.manager.views.sokovan.snapshot import SystemSnapshot
from ai.backend.manager.views.sokovan.workload import SessionWorkload

from .allocators.allocator import SchedulingAllocator
from .selectors.concentrated import ConcentratedAgentSelector
from .selectors.dispersed import DispersedAgentSelector
from .selectors.legacy import LegacyAgentSelector
from .selectors.roundrobin import RoundRobinAgentSelector
from .selectors.selector import (
    AgentLimit,
    AgentSelection,
    AgentSelectionCriteria,
    AgentSelector,
    AgentStateTracker,
    KernelResourceSpec,
    SessionMetadata,
)
from .sequencers.drf import DRFSequencer
from .sequencers.fair_share import FairShareSequencer
from .sequencers.fifo import FIFOSequencer
from .sequencers.lifo import LIFOSequencer
from .sequencers.sequencer import SchedulingSequencer, WorkloadSequencer
from .validators.validator import SchedulingValidator

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class SchedulingState:
    """Prepared state of one scheduling run, consumed by every later stage.

    ``snapshot`` captures the observed state plus the applicable policies
    (including the resource group's sequencer/selector pool keys);
    ``trackers`` and ``limit`` feed agent selection.
    """

    snapshot: SystemSnapshot
    trackers: Sequence[AgentStateTracker]
    limit: AgentLimit
    resource_group: ResourceGroupMeta


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
    _sequencer: SchedulingSequencer
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
        self._sequencer = SchedulingSequencer(self._make_sequencer_pool())
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
        pool["fair-share"] = FairShareSequencer(self._fair_share_repository)
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

    async def schedule_resource_group(
        self,
        scheduling_data: SchedulingData,
        provision_time: datetime,
    ) -> ScheduleResult:
        """
        Schedule sessions for a specific resource group.

        This method orchestrates the full provisioning pipeline using pre-fetched data:
        1. Sequencing: Order workloads using configured sequencer (FIFO/LIFO/DRF)
        2. Validation: Check quotas and constraints for each workload
        3. Agent selection: Select agents using configured strategy
        4. Allocation: Persist allocations to database

        Args:
            scheduling_data: Pre-fetched scheduling data from Handler.

        Returns:
            ScheduleResult containing scheduled session data
        """
        # Use data from scheduling_data instead of making DB calls
        base_workloads = scheduling_data.workloads
        resource_group = scheduling_data.resource_group
        resource_group_id = resource_group.id

        system_snapshot = scheduling_data.system_snapshot
        if system_snapshot is None:
            log.warning("Missing snapshot data for resource group {}", resource_group_id)
            return ScheduleResult(scheduled_session_ids=[], scheduling_failures=[])

        # Load per-session failed agents from Valkey for retry deprioritization,
        # inverted into a per-agent view for the state trackers below.
        # Uses a single pipelined Batch request instead of N parallel round-trips.
        failed_agents_list = await self._valkey_schedule.get_multiple_session_failed_agents([
            workload.session_id for workload in base_workloads
        ])
        failed_sessions_by_agent: dict[AgentId, set[SessionId]] = defaultdict(set)
        for workload, failed_agents in zip(base_workloads, failed_agents_list, strict=True):
            for agent_id in failed_agents:
                failed_sessions_by_agent[agent_id].add(workload.session_id)

        # Prepared run state, built once up front and consumed by every
        # later stage (sequencing, validation, agent selection, snapshot
        # updates). Observations stay immutable; in-batch allocations and
        # retry-failure hints live in the trackers.
        state = SchedulingState(
            snapshot=system_snapshot,
            resource_group=resource_group,
            trackers=[
                AgentStateTracker(
                    original_agent=agent.to_agent_info(),
                    failed_session_ids=frozenset(failed_sessions_by_agent.get(agent.id, ())),
                )
                for agent in system_snapshot.resource_group.resources.agents
            ],
            limit=AgentLimit(
                max_container_count=scheduling_data.max_container_count,
            ),
        )

        # Perform sequencing (batch operation for all workloads)
        # Record as shared phase so all entity records include it
        scheduler = state.snapshot.resource_group.policy.scheduler
        with (
            self._phase_metrics.measure_phase(
                "scheduler", resource_group_id, f"sequencing_{scheduler}"
            ),
            RecorderContext[SessionId].shared_phase(
                "sequencing", success_detail=self._sequencer.strategy_success_message(scheduler)
            ),
            RecorderContext[SessionId].shared_step(
                self._sequencer.strategy_name(scheduler),
                success_detail=self._sequencer.strategy_success_message(scheduler),
            ),
        ):
            sequenced_workloads = await self._sequencer.sequence(
                scheduler, resource_group_id, state.snapshot, base_workloads
            )
        session_allocations: list[SessionAllocation] = []
        scheduling_failures: list[SchedulingFailure] = []

        # Get current pool from RecorderContext (scope opened by coordinator)
        pool = RecorderContext[SessionId].current_pool()

        for session_workload in sequenced_workloads:
            try:
                # Sequencing phase is automatically included via shared phases
                session_allocation = await self._schedule_workload(
                    state,
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
                    last_try=provision_time,
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
            "Processing {} allocations and {} failures in resource group {}",
            len(session_allocations),
            len(scheduling_failures),
            resource_group_id,
        )
        # Create batch with allocations and failures
        batch = AllocationBatch(
            allocations=session_allocations,
            failures=scheduling_failures,
        )
        with self._phase_metrics.measure_phase("scheduler", resource_group_id, "allocation"):
            scheduled_session_ids = await self._allocator.allocate(batch)

        failure_ids = [f.session_id for f in scheduling_failures]
        await self._valkey_schedule.set_pending_queue(resource_group.name, failure_ids)
        return ScheduleResult(
            scheduled_session_ids=scheduled_session_ids,
            scheduling_failures=scheduling_failures,
        )

    async def _schedule_workload(
        self,
        state: SchedulingState,
        session_workload: SessionWorkload,
    ) -> SessionAllocation:
        resource_group_id = session_workload.resource_group_id
        agent_selector = self._agent_selector_pool[
            state.snapshot.resource_group.policy.agent_selection_strategy
        ]
        pool = RecorderContext[SessionId].current_pool()
        recorder = pool.recorder(session_workload.session_id)

        # Phase 1: Validation
        with self._phase_metrics.measure_phase("scheduler", resource_group_id, "validation"):
            with recorder.phase("validation"):
                self._validator.validate(state.snapshot, session_workload)

        # Phase 2: Agent Selection
        with self._phase_metrics.measure_phase("scheduler", resource_group_id, "agent_selection"):
            with recorder.phase(
                "agent_selection", success_detail=agent_selector.strategy_success_message()
            ):
                with recorder.step(
                    agent_selector.strategy_name(),
                    success_detail=agent_selector.strategy_success_message(),
                ):
                    session_allocation = await self._plan_workload(
                        state,
                        session_workload,
                    )

        # Phase 3: Allocation (prepare)
        with recorder.phase("allocation", success_detail=self._allocator.success_message()):
            with recorder.step(
                self._allocator.name(), success_detail=self._allocator.success_message()
            ):
                # Update the snapshot to reflect this allocation
                # Note: agent state changes are already committed into the trackers
                self._update_system_snapshot(
                    state.snapshot,
                    session_workload,
                )

        return session_allocation

    def _update_system_snapshot(
        self,
        snapshot: SystemSnapshot,
        workload: SessionWorkload,
    ) -> None:
        """
        Update the system snapshot after a session allocation.
        This ensures the next validation uses up-to-date information.

        Folding the workload's request advances both the slot reservations
        and the session counts of every owner scope.

        :param snapshot: The system snapshot to update (modified in-place)
        :param workload: The session workload that was allocated
        """
        snapshot.global_scope.occupancy.add_occupancy(
            workload.user_uuid,
            workload.project_id,
            workload.domain_id,
            workload.requested_slots,
        )

    async def _plan_workload(
        self,
        state: SchedulingState,
        session_workload: SessionWorkload,
    ) -> SessionAllocation:
        """
        Plan the agent placement of a single session workload.

        :param state: Prepared state of the scheduling run
        :param session_workload: The workload to place
        :return: SessionAllocation
        :raises AgentSelectionError: If agent selection fails
        """
        # Convert session workload to agent selection criteria
        criteria = self._build_selection_criteria(session_workload)

        # Selection commits state changes into the trackers on full success
        selector = self._agent_selector_pool[
            state.snapshot.resource_group.policy.agent_selection_strategy
        ]
        selections = await selector.select_agents_for_batch_requirements(
            state.trackers, criteria, state.limit
        )

        # Build session allocation from selections
        return self._build_session_allocation(
            session_workload, selections, state.resource_group.name
        )

    @staticmethod
    def _build_selection_criteria(workload: SessionWorkload) -> AgentSelectionCriteria:
        """Project one session workload into agent selection criteria."""
        return AgentSelectionCriteria(
            session_metadata=SessionMetadata(
                session_id=workload.session_id,
                session_type=workload.session_type,
                resource_group_id=workload.resource_group_id,
                cluster_mode=workload.cluster_mode,
            ),
            kernel_requirements={
                kernel.kernel_id: KernelResourceSpec(
                    requested_slots=kernel.requested_slots,
                    required_architecture=kernel.architecture,
                )
                for kernel in workload.kernels
            },
            agent_selection_policy=workload.agent_selection_policy,
            designated_agent_ids=workload.designated_agent_ids,
        )

    @staticmethod
    def _build_session_allocation(
        session_workload: SessionWorkload,
        selections: list[AgentSelection],
        resource_group_name: ResourceGroupName,
    ) -> SessionAllocation:
        """Build a SessionAllocation from agent selection results."""
        kernel_allocations: list[KernelAllocation] = []
        agent_allocation_map: dict[AgentId, AgentAllocation] = {}

        for selection in selections:
            resource_req = selection.resource_requirements
            selected_agent = selection.selected_agent

            # Track resource allocation for this agent
            if selected_agent.agent_id not in agent_allocation_map:
                agent_allocation_map[selected_agent.agent_id] = AgentAllocation(
                    agent_id=selected_agent.agent_id,
                    allocated_slots=[],
                )
            # The allocation write path still speaks ResourceSlot; convert at
            # this boundary only.
            agent_allocation_map[selected_agent.agent_id].allocated_slots.append(
                ResourceSlot({str(k): v for k, v in resource_req.requested_slots.slots.items()})
            )

            # Create kernel allocations
            for kernel_id in resource_req.kernel_ids:
                kernel_allocations.append(
                    KernelAllocation(
                        kernel_id=kernel_id,
                        agent_id=selected_agent.agent_id,
                        agent_addr=selected_agent.agent_addr,
                        resource_group_name=resource_group_name,
                        resource_group_id=session_workload.resource_group_id,
                    )
                )

        agent_allocations = list(agent_allocation_map.values())

        return SessionAllocation(
            session_id=session_workload.session_id,
            session_type=session_workload.session_type,
            cluster_mode=session_workload.cluster_mode,
            resource_group_name=resource_group_name,
            resource_group_id=session_workload.resource_group_id,
            kernel_allocations=kernel_allocations,
            agent_allocations=agent_allocations,
            access_key=session_workload.access_key,
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
