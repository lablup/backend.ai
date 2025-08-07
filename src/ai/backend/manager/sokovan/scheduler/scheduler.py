import logging
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from ai.backend.common.types import AgentId, AgentSelectionStrategy, ResourceSlot, SessionId
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
    SessionAllocation,
    SessionWorkload,
    SystemSnapshot,
)
from .validators.validator import SchedulingValidator

if TYPE_CHECKING:
    from ai.backend.manager.repositories.schedule.repository import (
        ScheduleRepository,
        SchedulingContextData,
    )

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
            with self._operation_metrics.measure_operation("schedule_all_scaling_groups"):
                # Get all schedulable scaling groups from repository
                scaling_groups = await self._repository.get_schedulable_scaling_groups()
                for scaling_group in scaling_groups:
                    try:
                        log.trace("Scheduling sessions for scaling group: {}", scaling_group)
                        # Schedule sessions for this scaling group
                        with self._operation_metrics.measure_operation(
                            f"schedule_scaling_group_{scaling_group}"
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
        # Single optimized call to get all scheduling context data
        # This consolidates: get_scaling_group_info_for_sokovan, get_pending_sessions,
        # get_system_snapshot, and get_scheduling_config into ONE DB session
        context = await self._repository.get_scheduling_context_data(scaling_group)

        if context is None:
            log.trace(
                "No pending sessions for scaling group {}. Skipping scheduling.",
                scaling_group,
            )
            return 0

        # Schedule using the context data - no more DB calls needed
        return await self._schedule_queued_sessions_with_context(scaling_group, context)

    async def _schedule_queued_sessions_with_context(
        self, scaling_group: str, context: "SchedulingContextData"
    ) -> int:
        """
        Schedule all queued sessions using pre-fetched context data.
        No database calls are made in this method - all data comes from context.

        :param scaling_group: The scaling group to schedule for
        :param context: Pre-fetched context containing all necessary data
        :return: The number of sessions successfully scheduled
        """
        # Use data from context instead of making DB calls
        workloads = context.pending_sessions
        sg_info = context.scaling_group_info
        system_snapshot = context.system_snapshot
        config = context.scheduling_config

        selection_config = AgentSelectionConfig(
            max_container_count=config.max_container_count_per_agent,
            enforce_spreading_endpoint_replica=config.enforce_spreading_endpoint_replica,
        )
        with self._phase_metrics.measure_phase(
            scaling_group, f"sequencing_{sg_info.scheduler_name}"
        ):
            sequencer = self._sequencer_pool[sg_info.scheduler_name]
            sequenced_workloads = await sequencer.sequence(system_snapshot, workloads)

        mutable_agents = context.agents
        session_allocations: list[SessionAllocation] = []
        agent_selector = self._agent_selector_pool[sg_info.agent_selection_strategy]
        for session_workload in sequenced_workloads:
            try:
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
                    "Validation failed for workload {}: {}",
                    session_workload.session_id,
                    e,
                )
                continue
        # Allocate resources for each validated workload
        if session_allocations:
            log.info(
                "Allocating resources for {} session allocations in scaling group {}",
                len(session_allocations),
                scaling_group,
            )
            with self._phase_metrics.measure_phase(scaling_group, "allocation"):
                await self._allocator.allocate(session_allocations)

        return len(session_allocations)

    async def _schedule_workload(
        self,
        scaling_group: str,
        mutable_snapshot: SystemSnapshot,
        mutable_agents: Sequence[AgentInfo],
        selection_config: AgentSelectionConfig,
        agent_selector: AgentSelector,
        session_workload: SessionWorkload,
    ) -> SessionAllocation:
        with self._phase_metrics.measure_phase(scaling_group, "validation"):
            self._validator.validate(mutable_snapshot, session_workload)

        with self._phase_metrics.measure_phase(scaling_group, "agent_selection"):
            session_allocation = await self._allocate_workload(
                session_workload,
                mutable_agents,
                selection_config,
                scaling_group,
                agent_selector,
            )

        # Update the snapshot to reflect this allocation
        # Note: agent state changes are already applied to mutable_agents by select_agents_for_batch_requirements
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
        current_keypair = snapshot.resource_occupancy.by_keypair.get(
            workload.access_key, ResourceSlot()
        )
        snapshot.resource_occupancy.by_keypair[workload.access_key] = (
            current_keypair + total_allocated_slots
        )

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
        :raises NoResourceRequirementsError: If no resource requirements found
        """
        # Convert to new criteria format
        criteria = session_workload.to_agent_selection_criteria()

        # Use batch selection method - it will get resource requirements internally
        # and apply state changes to agents_info
        selections = await agent_selector.select_agents_for_batch_requirements(
            agents_info,
            criteria,
            selection_config,
            session_workload.designated_agent,
        )

        # Build kernel allocations and agent allocations from selections
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

        # Create session allocation
        agent_allocations = list(agent_allocation_map.values())

        session_allocation = SessionAllocation(
            session_id=session_workload.session_id,
            session_type=session_workload.session_type,
            cluster_mode=session_workload.cluster_mode,
            scaling_group=scaling_group,
            kernel_allocations=kernel_allocations,
            agent_allocations=agent_allocations,
        )

        return session_allocation

    # ========== Lifecycle Management Methods ==========
    # These methods will be refactored into separate lifecycle modules in the future,
    # but are included here for now to maintain consistency with the scheduling logic.

    async def check_preconditions_all(self) -> int:
        """
        Check preconditions for all SCHEDULED sessions.
        This includes checking and pulling required images.

        Returns:
            int: The number of sessions that passed precondition checks.
        """
        lock_lifetime = (
            self._config_provider.config.manager.session_check_precondition_lock_lifetime
        )
        total_processed = 0

        async with self._lock_factory(LockID.LOCKID_CHECK_PRECOND, lock_lifetime):
            with self._operation_metrics.measure_operation("check_preconditions_all"):
                # Get SCHEDULED sessions with minimal data
                sessions = await self._repository.get_scheduled_sessions_for_precond()

                if not sessions:
                    log.debug("check_preconditions_all(): No SCHEDULED sessions found")
                    return 0

                log.debug(
                    "check_preconditions_all(): Processing {} SCHEDULED sessions", len(sessions)
                )

                # Process preconditions
                total_processed = await self._process_preconditions(sessions)

                if total_processed > 0:
                    log.info("check_preconditions_all(): Processed {} sessions", total_processed)

                return total_processed

    async def _process_preconditions(self, sessions: list) -> int:
        """
        Internal method to process precondition checks for sessions.

        This method:
        1. Creates kernel-agent bindings for image checks
        2. Initiates image pull tasks on agents
        3. Transitions sessions to PREPARING state

        Args:
            sessions: List of SessionRow objects with SCHEDULED status

        Returns:
            int: Number of sessions successfully processed
        """
        from ai.backend.manager.scheduler.types import AgentAllocationContext, KernelAgentBinding

        if not sessions:
            return 0

        # Create kernel-agent bindings for image check
        bindings = []
        for session in sessions:
            if not hasattr(session, "kernels") or not session.kernels:
                log.warning("Session {} has no kernels, skipping precondition check", session.id)
                continue

            for kernel in session.kernels:
                if kernel.agent and kernel.agent_addr:
                    bindings.append(
                        KernelAgentBinding(
                            kernel=kernel,
                            agent_alloc_ctx=AgentAllocationContext(
                                agent_id=kernel.agent,
                                agent_addr=kernel.agent_addr,
                                scaling_group=session.scaling_group_name,
                            ),
                            allocated_host_ports=set(),
                        )
                    )

        if not bindings:
            log.warning("No valid kernel-agent bindings found for precondition check")
            return 0

        # NOTE: check_and_pull_images is handled by the AgentRegistry
        # which should be called from the dispatcher/orchestrator level
        # Here we just transition the sessions to PREPARING state

        # Collect session IDs for state transition
        session_ids = [session.id for session in sessions if session.id]

        # Transit sessions to PREPARING state
        if session_ids:
            await self._repository.transit_sessions_to_preparing(session_ids)
            log.debug("Transitioned {} sessions from SCHEDULED to PREPARING", len(session_ids))

        return len(session_ids)

    async def start_sessions_all(self) -> int:
        """
        Start all PREPARED sessions by creating containers on agents.
        This transitions sessions from PREPARED to CREATING state.

        Returns:
            int: The number of sessions that were started.
        """
        lock_lifetime = self._config_provider.config.manager.session_start_lock_lifetime
        total_started = 0

        async with self._lock_factory(LockID.LOCKID_START, lock_lifetime):
            with self._operation_metrics.measure_operation("start_sessions_all"):
                # Get PREPARED sessions and mark them as CREATING
                sessions = await self._repository.mark_sessions_and_kernels_creating_sokovan()

                if not sessions:
                    log.debug("start_sessions_all(): No PREPARED sessions found")
                    return 0

                log.debug("start_sessions_all(): Starting {} sessions", len(sessions))

                # Start sessions - actual container creation
                total_started = await self._start_sessions(sessions)

                if total_started > 0:
                    log.info("start_sessions_all(): Started {} sessions", total_started)

                return total_started

    async def _start_sessions(self, sessions: list) -> int:
        """
        Internal method to prepare sessions for starting.
        Sessions are already in CREATING state.

        The actual container creation is handled by the AgentRegistry.start_session()
        method which is called from the dispatcher/orchestrator level.

        Args:
            sessions: List of SessionRow objects already in CREATING status

        Returns:
            int: Number of sessions successfully prepared for starting
        """
        if not sessions:
            return 0

        # NOTE: The actual start_session RPC calls to agents are handled
        # by the AgentRegistry which should be called from the dispatcher/orchestrator level.
        # Sessions are already in CREATING state from mark_sessions_and_kernels_creating_sokovan()

        # The dispatcher will pick up these CREATING sessions and call AgentRegistry.start_session()
        # for each one to actually create the containers on the agents.

        return len(sessions)

    async def enqueue_session_to_destroy(
        self, session_id: SessionId, reason: Optional[str] = None
    ) -> bool:
        """
        Enqueue a session for destruction by marking it as TERMINATING.
        This is the first step in the graceful session termination process.

        Args:
            session_id: The session to enqueue for destruction
            reason: Optional reason for termination

        Returns:
            bool: True if the session was successfully enqueued, False otherwise
        """
        with self._operation_metrics.measure_operation("enqueue_session_to_destroy"):
            # Mark the session as TERMINATING
            success = await self._repository.mark_session_terminating(session_id, reason)

            if success:
                log.info(
                    "enqueue_session_to_destroy(): Session {} marked for termination", session_id
                )
                # Note: The actual destruction will be handled by destroy_sessions_all()
                # which processes all TERMINATING sessions
            else:
                log.warning(
                    "enqueue_session_to_destroy(): Failed to mark session {} for termination",
                    session_id,
                )

            return success

    async def destroy_sessions_all(self) -> int:
        """
        Destroy all sessions that are marked as TERMINATING.
        This transitions sessions from TERMINATING to TERMINATED state.

        Returns:
            int: The number of sessions that were destroyed.
        """
        lock_lifetime = 30.0  # Default lock lifetime for destroy operation
        total_destroyed = 0

        async with self._lock_factory(LockID.LOCKID_SCHEDULE, lock_lifetime):
            with self._operation_metrics.measure_operation("destroy_sessions_all"):
                # Get TERMINATING sessions
                sessions = await self._repository.get_sessions_to_terminate()

                if not sessions:
                    log.debug("destroy_sessions_all(): No TERMINATING sessions found")
                    return 0

                log.debug(
                    "destroy_sessions_all(): Processing {} TERMINATING sessions", len(sessions)
                )

                # Destroy sessions
                total_destroyed = await self._destroy_sessions(sessions)

                if total_destroyed > 0:
                    log.info("destroy_sessions_all(): Destroyed {} sessions", total_destroyed)

                return total_destroyed

    async def _destroy_sessions(self, sessions: list) -> int:
        """
        Internal method to destroy sessions.

        The actual container destruction is handled by the AgentRegistry.destroy_session()
        method which is called from the dispatcher/orchestrator level.

        Args:
            sessions: List of SessionRow objects with TERMINATING status

        Returns:
            int: Number of sessions successfully destroyed
        """
        if not sessions:
            return 0

        # NOTE: The actual destroy_session RPC calls to agents are handled
        # by the AgentRegistry which should be called from the dispatcher/orchestrator level.
        # Here we just prepare the data for destruction.

        # Collect session IDs for destruction
        session_ids = [session.id for session in sessions if session.id]

        if session_ids:
            log.debug("Prepared {} sessions for destruction", len(session_ids))

        return len(session_ids)
