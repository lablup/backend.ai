import asyncio
import logging
import time
from collections import defaultdict
from collections.abc import Coroutine, Mapping, Sequence
from dataclasses import dataclass, field
from itertools import groupby
from typing import Any, Awaitable, Optional

import aiotools
import async_timeout
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.docker import ImageRef
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.types import (
    AgentId,
    AgentSelectionStrategy,
    AutoPullBehavior,
    ClusterInfo,
    ClusterMode,
    ClusterSSHKeyPair,
    ClusterSSHPortMapping,
    ImageConfig,
    KernelCreationConfig,
    KernelId,
    ResourceSlot,
    SessionId,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.clients.agent import AgentPool
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.defs import SERVICE_MAX_RETRIES, START_SESSION_TIMEOUT_SEC
from ai.backend.manager.exceptions import convert_to_status_data
from ai.backend.manager.metrics.scheduler import (
    SchedulerPhaseMetricObserver,
)
from ai.backend.manager.models.network import NetworkType
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.repositories.scheduler import (
    KernelTerminationResult,
    SchedulerRepository,
    SchedulingData,
    TerminatingKernelData,
)
from ai.backend.manager.scheduler.types import ScheduleType
from ai.backend.manager.types import DistributedLockFactory

from .allocators.allocator import SchedulingAllocator
from .hooks.registry import HookRegistry, HookRegistryArgs
from .results import ScheduledSessionData, ScheduleResult
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
from .types import (
    AllocationBatch,
    ImageConfigData,
    KernelBindingData,
    KeypairOccupancy,
    NetworkSetup,
    SchedulingConfig,
    SchedulingFailure,
    SchedulingPredicate,
    SessionAllocation,
    SessionDataForPull,
    SessionDataForStart,
    SessionRunningData,
    SessionWorkload,
    SystemSnapshot,
)
from .validators.validator import SchedulingValidator

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class AgentTerminationGroup:
    """Groups kernels by agent for batch termination."""

    agent_id: Optional[AgentId]
    agent_addr: Optional[str]
    kernels: list[TerminatingKernelData] = field(default_factory=list)


@dataclass
class SchedulerArgs:
    validator: SchedulingValidator
    sequencer: WorkloadSequencer
    agent_selector: AgentSelector
    allocator: SchedulingAllocator
    repository: SchedulerRepository
    deployment_repository: DeploymentRepository
    config_provider: ManagerConfigProvider
    lock_factory: DistributedLockFactory
    agent_pool: AgentPool
    network_plugin_ctx: NetworkPluginContext
    event_producer: EventProducer
    valkey_schedule: ValkeyScheduleClient


class Scheduler:
    _validator: SchedulingValidator
    _default_sequencer: WorkloadSequencer
    _default_agent_selector: AgentSelector
    _allocator: SchedulingAllocator
    _repository: SchedulerRepository
    _config_provider: ManagerConfigProvider
    _lock_factory: DistributedLockFactory
    _agent_pool: AgentPool
    _network_plugin_ctx: NetworkPluginContext
    _sequencer_pool: Mapping[str, WorkloadSequencer]
    _agent_selector_pool: Mapping[AgentSelectionStrategy, AgentSelector]
    _phase_metrics: SchedulerPhaseMetricObserver
    _hook_registry: HookRegistry

    _valkey_schedule: ValkeyScheduleClient  # TODO: Remove this client and use only via repository

    def __init__(self, args: SchedulerArgs) -> None:
        self._validator = args.validator
        self._default_sequencer = args.sequencer
        self._default_agent_selector = args.agent_selector
        self._allocator = args.allocator
        self._repository = args.repository
        self._config_provider = args.config_provider
        self._lock_factory = args.lock_factory
        self._agent_pool = args.agent_pool
        self._network_plugin_ctx = args.network_plugin_ctx
        self._sequencer_pool = self._make_sequencer_pool()
        self._agent_selector_pool = self._make_agent_selector_pool(
            args.config_provider.config.manager.agent_selection_resource_priority
        )
        self._phase_metrics = SchedulerPhaseMetricObserver.instance()
        self._hook_registry = HookRegistry(
            HookRegistryArgs(
                repository=args.deployment_repository,
                agent_pool=args.agent_pool,
                network_plugin_ctx=args.network_plugin_ctx,
                config_provider=args.config_provider,
                event_producer=args.event_producer,
            )
        )
        self._valkey_schedule = args.valkey_schedule

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

    async def schedule_all_scaling_groups(self) -> ScheduleResult:
        """
        Schedule sessions for all scaling groups.

        Returns:
            ScheduleResult: Result of the scheduling operation.
        """
        all_scheduled_sessions: list[ScheduledSessionData] = []
        # Get all schedulable scaling groups from repository
        scaling_groups = await self._repository.get_schedulable_scaling_groups()
        for scaling_group in scaling_groups:
            try:
                log.trace("Scheduling sessions for scaling group: {}", scaling_group)
                # Schedule sessions for this scaling group
                with self._phase_metrics.measure_phase("scheduler", scaling_group, "scheduling"):
                    scheduled_result = await self._schedule_scaling_group(scaling_group)
                all_scheduled_sessions.extend(scheduled_result.scheduled_sessions)
                if scheduled_result.scheduled_sessions:
                    log.info(
                        "Scheduled {} sessions for scaling group: {}",
                        len(scheduled_result.scheduled_sessions),
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

        return ScheduleResult(scheduled_sessions=all_scheduled_sessions)

    async def _schedule_scaling_group(self, scaling_group: str) -> ScheduleResult:
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
        agent_selection_strategy = sg_info.scheduler_opts.config.get(
            "agent_selection_strategy", AgentSelectionStrategy.CONCENTRATED
        )
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
                selector_strategy = agent_selector._strategy
                passed_phases.append(
                    SchedulingPredicate(
                        name=selector_strategy.name(), msg=selector_strategy.success_message()
                    )
                )
            except Exception as e:
                # Add failed predicate for agent selection
                selector_strategy = agent_selector._strategy
                failed_phases.append(SchedulingPredicate(name=selector_strategy.name(), msg=str(e)))
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

    async def terminate_sessions(self) -> ScheduleResult:
        """
        Send termination requests to all agents for sessions marked as TERMINATING.

        This method only sends RPC calls to agents. Actual status updates are handled by:
        - Agent event callbacks (for successful terminations)
        - sweep_lost_agent_kernels() (for lost agents or failed RPC calls)

        Returns:
            Empty ScheduleResult (no status updates performed here)
        """
        # Fetch all terminating sessions
        terminating_sessions = await self._repository.get_terminating_sessions()

        if not terminating_sessions:
            log.debug("No sessions to terminate")
            return ScheduleResult()

        log.info("Processing {} sessions for termination", len(terminating_sessions))

        # Collect all termination tasks from all sessions
        all_tasks: list[Awaitable[KernelTerminationResult]] = []
        skipped_kernels = 0

        for session in terminating_sessions:
            for kernel in session.kernels:
                # Only process kernels with assigned agents
                if kernel.agent_id:
                    task = self._terminate_kernel(
                        kernel.agent_id,
                        str(kernel.kernel_id),
                        str(session.session_id),
                        session.status_info,
                        kernel.occupied_slots,
                    )
                    all_tasks.append(task)
                else:
                    # Kernel has no agent assigned - needs sweep
                    skipped_kernels += 1

        # If there are kernels without agents, trigger sweep
        if skipped_kernels > 0:
            log.info(
                "Found {} kernels without agents, requesting sweep",
                skipped_kernels,
            )
            await self._valkey_schedule.mark_schedule_needed(
                ScheduleType.SWEEP_LOST_AGENT_KERNELS.value
            )

        # Execute all termination tasks concurrently across all sessions
        if not all_tasks:
            log.debug("No kernels with agents to terminate")
            return ScheduleResult()

        log.info("Terminating {} kernels in parallel", len(all_tasks))

        # Use gather with return_exceptions to ensure partial failures don't block others
        results = await asyncio.gather(*all_tasks, return_exceptions=True)

        # Log results but don't update DB (handled by events and sweep)
        success_count = 0
        failed_count = 0
        for r in results:
            if isinstance(r, BaseException):
                failed_count += 1
                continue
            if not r.success:
                failed_count += 1
                continue
            success_count += 1

        log.info(
            "Termination RPC calls completed: {} successful, {} failed",
            success_count,
            failed_count,
        )

        return ScheduleResult()

    async def _terminate_kernel(
        self,
        agent_id: AgentId,
        kernel_id: str,
        session_id: str,
        reason: str,
        occupied_slots: ResourceSlot,
    ) -> KernelTerminationResult:
        """
        Terminate a single kernel on an agent.

        :param agent_id: The agent ID where the kernel is running
        :param kernel_id: The kernel ID to terminate
        :param session_id: The session ID that owns the kernel
        :param reason: The reason for termination
        :return: KernelTerminationResult with success status
        """
        try:
            agent_client = self._agent_pool.get_agent_client(agent_id)

            # Call agent's destroy_kernel RPC method with correct parameters
            await agent_client.destroy_kernel(kernel_id, session_id, reason, suppress_events=False)
            return KernelTerminationResult(
                kernel_id=kernel_id,
                agent_id=agent_id,
                occupied_slots=occupied_slots,
                success=True,
            )
        except Exception as e:
            log.warning(
                "Failed to terminate kernel {} on agent {}: {}",
                kernel_id,
                agent_id,
                e,
            )

            return KernelTerminationResult(
                kernel_id=kernel_id,
                agent_id=agent_id,
                occupied_slots=occupied_slots,
                success=False,
                error=str(e),
            )

    async def sweep_stale_sessions(self) -> ScheduleResult:
        """
        Sweep stale sessions including those with pending timeout.
        This is a maintenance operation, not a scheduling operation.

        Note: The actual marking of sessions for termination should be done
        through SchedulingController.mark_sessions_for_termination() by the coordinator.

        :return: ScheduleResult with the count of swept sessions
        """
        # Get sessions that have exceeded their pending timeout
        timed_out_sessions = await self._repository.get_pending_timeout_sessions()

        if timed_out_sessions:
            # Extract session IDs
            session_ids = [session.session_id for session in timed_out_sessions]

            log.info(
                "Found {} sessions with pending timeout that need termination",
                len(session_ids),
            )

            # Note: The coordinator should call SchedulingController.mark_sessions_for_termination()
            # with these session_ids. This method just identifies the sessions.
            # For now, we'll directly mark them through repository for backward compatibility
            await self._repository.mark_sessions_terminating(
                session_ids,
                reason="PENDING_TIMEOUT",
            )

            # Convert swept sessions to ScheduledSessionData format
            scheduled_data = [
                ScheduledSessionData(
                    session_id=session.session_id,
                    creation_id=session.creation_id,
                    access_key=session.access_key,
                    reason="sweeped-as-stale",
                )
                for session in timed_out_sessions
            ]
            return ScheduleResult(scheduled_sessions=scheduled_data)

        return ScheduleResult()

    async def sweep_lost_agent_kernels(self) -> ScheduleResult:
        """
        Sweep kernels in TERMINATING sessions that cannot be terminated normally.

        This handles kernels where:
        - Agent is LOST
        - Agent is None (never assigned)

        These kernels are directly marked as TERMINATED without RPC calls.
        This is a cleanup operation separate from normal termination.
        Only kernel status is updated; session status updates are handled
        by other mechanisms when all kernels are terminated.

        Returns:
            ScheduleResult (empty - no scheduled sessions)
        """
        # Fetch kernels with lost or missing agents
        lost_kernels = await self._repository.get_terminating_kernels_with_lost_agents()

        if not lost_kernels:
            log.debug("No lost agent kernels to sweep")
            return ScheduleResult()

        log.info(
            "Sweeping {} kernels with lost/missing agents",
            len(lost_kernels),
        )

        # Build kernel results
        kernel_results: list[KernelTerminationResult] = []

        for kernel in lost_kernels:
            log.info(
                "Sweeping kernel {} in session {} (agent: {}, agent_status: {})",
                kernel.kernel_id,
                kernel.session_id,
                kernel.agent_id,
                kernel.agent_status,
            )

            # Mark as successfully terminated since agent is gone
            kernel_result = KernelTerminationResult(
                kernel_id=kernel.kernel_id,
                agent_id=kernel.agent_id,
                occupied_slots=ResourceSlot(),  # Empty since agent is lost/missing
                success=True,
            )
            kernel_results.append(kernel_result)

        # Batch update all swept kernels (sessions will be updated by other handlers)
        await self._repository.batch_update_kernels_terminated(
            kernel_results,
            reason="swept-lost-agent",
        )

        log.info("Successfully swept {} kernels", len(kernel_results))

        # Request check-terminating-progress to update session status
        await self._valkey_schedule.mark_schedule_needed(
            ScheduleType.CHECK_TERMINATING_PROGRESS.value
        )

        return ScheduleResult()

    async def check_pulling_progress(self) -> ScheduleResult:
        """
        Check if sessions in PULLING or PREPARING state have all kernels ready to progress.
        Sessions with all kernels that have reached PREPARED state can move to PREPARED phase.

        :return: ScheduleResult with the count of sessions that progressed
        """
        # Get sessions with all kernels that have reached PREPARED state
        # Check both PREPARING and PULLING statuses
        sessions_data = await self._repository.get_sessions_for_transition(
            [SessionStatus.PREPARING, SessionStatus.PULLING],
            [KernelStatus.PREPARED, KernelStatus.RUNNING],
        )

        if not sessions_data:
            return ScheduleResult()

        sessions_to_update = [session.session_id for session in sessions_data]
        if sessions_to_update:
            await self._repository.update_sessions_to_prepared(sessions_to_update)
            # Convert updated sessions to ScheduledSessionData format
            scheduled_data = [
                ScheduledSessionData(
                    session_id=session.session_id,
                    creation_id=session.creation_id,
                    access_key=session.access_key,
                    reason="triggered-by-scheduler",
                )
                for session in sessions_data
            ]
            return ScheduleResult(scheduled_sessions=scheduled_data)
        return ScheduleResult()

    async def check_creating_progress(self) -> ScheduleResult:
        """
        Check if sessions in CREATING/PREPARING state have all kernels RUNNING.
        Sessions with all kernels RUNNING can transition to RUNNING state.

        :return: ScheduleResult with the count of sessions that transitioned to RUNNING
        """
        sessions_data = await self._repository.get_sessions_for_transition(
            [SessionStatus.CREATING],
            [KernelStatus.RUNNING],
        )

        if not sessions_data:
            return ScheduleResult()

        sessions_running_data: list[SessionRunningData] = []

        hook_coroutines = [
            self._hook_registry.get_hook(session_data.session_type).on_transition_to_running(
                session_data
            )
            for session_data in sessions_data
        ]

        hook_results = await asyncio.gather(*hook_coroutines, return_exceptions=True)

        for session_data, result in zip(sessions_data, hook_results):
            if isinstance(result, BaseException):
                log.error(
                    "Hook failed with exception for session {}: {}",
                    session_data.session_id,
                    result,
                )
                continue

            # Calculate total occupying_slots from all kernels
            total_occupying_slots = ResourceSlot()
            for kernel in session_data.kernels:
                if kernel.occupied_slots:
                    total_occupying_slots += kernel.occupied_slots

            sessions_running_data.append(
                SessionRunningData(
                    session_id=session_data.session_id,
                    occupying_slots=total_occupying_slots,
                )
            )

        if sessions_running_data:
            await self._repository.update_sessions_to_running(sessions_running_data)
            # Convert updated sessions to ScheduledSessionData format
            scheduled_data = [
                ScheduledSessionData(
                    session_id=session_data.session_id,
                    creation_id=session_data.creation_id,
                    access_key=session_data.access_key,
                    reason="triggered-by-scheduler",
                )
                for session_data in sessions_data
                if any(srd.session_id == session_data.session_id for srd in sessions_running_data)
            ]
            return ScheduleResult(scheduled_sessions=scheduled_data)

        return ScheduleResult()

    async def check_terminating_progress(self) -> ScheduleResult:
        """
        Check if sessions in TERMINATING state have all kernels TERMINATED.
        Sessions with all kernels TERMINATED can transition to TERMINATED state.

        :return: ScheduleResult with the count of sessions that transitioned to TERMINATED
        """
        sessions_data = await self._repository.get_sessions_for_transition(
            [SessionStatus.TERMINATING],
            [KernelStatus.TERMINATED],
        )

        if not sessions_data:
            return ScheduleResult()

        sessions_to_update: list[SessionId] = []
        log.info("session types to terminate: {}", [s.session_type for s in sessions_data])

        hook_coroutines = [
            self._hook_registry.get_hook(session_data.session_type).on_transition_to_terminated(
                session_data
            )
            for session_data in sessions_data
        ]

        hook_results = await asyncio.gather(*hook_coroutines, return_exceptions=True)

        for session_data, result in zip(sessions_data, hook_results):
            if isinstance(result, BaseException):
                log.error(
                    "Termination hook failed with exception for session {} (will still terminate): {}",
                    session_data.session_id,
                    result,
                )
            sessions_to_update.append(session_data.session_id)

        if sessions_to_update:
            await self._repository.update_sessions_to_terminated(sessions_to_update)
            # Convert updated sessions to ScheduledSessionData format
            scheduled_data = [
                ScheduledSessionData(
                    session_id=session.session_id,
                    creation_id=session.creation_id,
                    access_key=session.access_key,
                    reason=session.status_info or "unknown",
                )
                for session in sessions_data
                if session.session_id in sessions_to_update
            ]
            return ScheduleResult(scheduled_sessions=scheduled_data)

        return ScheduleResult()

    async def check_preconditions(self) -> ScheduleResult:
        """
        Check preconditions for scheduled sessions.
        Transitions sessions from SCHEDULED to PREPARING and triggers image pulling.

        :return: ScheduleResult with the count of sessions transitioned
        """
        # Get scheduled sessions for image pulling
        result = await self._repository.get_sessions_for_pull(
            [SessionStatus.SCHEDULED],
            [
                KernelStatus.SCHEDULED,
            ],
        )
        scheduled_sessions = result.sessions
        image_configs = result.image_configs

        if not scheduled_sessions:
            return ScheduleResult()

        # Extract session IDs for status update
        session_ids = [s.session_id for s in scheduled_sessions]

        # Update sessions to PREPARING status
        await self._repository.update_sessions_to_preparing(session_ids)

        # Trigger image checking and pulling on agents
        await self._trigger_image_pulling_for_sessions(scheduled_sessions, image_configs)

        # Convert to ScheduledSessionData format
        scheduled_data = [
            ScheduledSessionData(
                session_id=session.session_id,
                creation_id=session.creation_id,
                access_key=session.access_key,
                reason="passed-preconditions",
            )
            for session in scheduled_sessions
        ]
        return ScheduleResult(scheduled_sessions=scheduled_data)

    async def _trigger_image_pulling_for_sessions(
        self,
        sessions: list[SessionDataForPull],
        image_configs: dict[str, ImageConfigData],
    ) -> None:
        """
        Trigger image checking and pulling on agents for the given sessions.

        :param sessions: List of sessions with kernels
        :param image_configs: Image configurations indexed by image name
        """
        auto_pull = self._config_provider.config.docker.image.auto_pull.value

        # Group kernels by agent for image pulling
        agent_image_configs: defaultdict[AgentId, dict[str, ImageConfig]] = defaultdict(dict)

        # Build agent_image_configs by directly looking up configs
        for session in sessions:
            for kernel in session.kernels:
                agent_id = kernel.agent_id
                if agent_id:
                    # Image config must exist since we queried based on kernels
                    img_cfg = image_configs[kernel.image]

                    # Convert ImageConfigData to ImageConfig format
                    # Use canonical as key for agent_image_configs to avoid duplicates
                    canonical = img_cfg.canonical
                    if canonical not in agent_image_configs[agent_id]:
                        image_config = img_cfg.to_image_config(AutoPullBehavior(auto_pull))
                        agent_image_configs[agent_id][canonical] = image_config

        # Trigger image checking and pulling on each agent
        pull_tasks: list[Coroutine[Any, Any, Mapping[str, str]]] = []
        for agent_id, agent_images in agent_image_configs.items():
            agent_client = self._agent_pool.get_agent_client(agent_id)
            pull_tasks.append(agent_client.check_and_pull(agent_images))

        if pull_tasks:
            await asyncio.gather(*pull_tasks, return_exceptions=True)

    async def start_sessions(self) -> ScheduleResult:
        """
        Start sessions that have passed precondition checks.
        Transitions sessions from PREPARED to CREATING and starts kernels on agents.

        :return: ScheduleResult with the count of sessions started
        """
        # Get prepared sessions for starting
        sessions_with_images = await self._repository.get_sessions_for_start(
            [SessionStatus.PREPARED],
            [
                KernelStatus.PREPARED,
            ],
        )
        prepared_sessions = sessions_with_images.sessions
        image_configs = sessions_with_images.image_configs

        if not prepared_sessions:
            return ScheduleResult()
        # Extract session IDs for status update
        session_ids = [s.session_id for s in prepared_sessions]

        # Update sessions and kernels to CREATING status
        await self._repository.update_sessions_and_kernels_to_creating(session_ids)

        # Start sessions concurrently
        await self._start_sessions_concurrently(prepared_sessions, image_configs)

        # Convert prepared sessions to ScheduledSessionData format
        scheduled_data = [
            ScheduledSessionData(
                session_id=session.session_id,
                creation_id=session.creation_id,
                access_key=session.access_key,
                reason="triggered-by-scheduler",
            )
            for session in prepared_sessions
        ]
        return ScheduleResult(scheduled_sessions=scheduled_data)

    async def _start_sessions_concurrently(
        self,
        sessions: list[SessionDataForStart],
        image_configs: dict[str, ImageConfigData],
    ) -> None:
        """
        Start multiple sessions concurrently with timeout.

        :param sessions: List of sessions to start
        :param image_configs: Image configurations for the sessions
        """
        # Start each session concurrently with timeout
        async with (
            async_timeout.timeout(delay=START_SESSION_TIMEOUT_SEC),
            aiotools.PersistentTaskGroup() as tg,
        ):
            for session in sessions:
                # Start session asynchronously with image configs
                tg.create_task(self._start_single_session(session, image_configs))

    async def _start_single_session(
        self,
        session: SessionDataForStart,
        image_configs: dict[str, ImageConfigData],
    ) -> None:
        """
        Start a single session by creating kernels on agents.

        :param session: Session data to start
        :param image_configs: Image configurations for the session
        """
        log_fmt = "start-session(s:{}, type:{}, name:{}, ak:{}, cluster_mode:{}): "
        log_args = (
            session.session_id,
            session.session_type,
            session.name,
            session.access_key,
            session.cluster_mode,
        )
        log.debug(log_fmt + "try-starting", *log_args)

        try:
            # Ensure we have kernels to start
            if len(session.kernels) == 0:
                raise ValueError(f"Session {session.session_id} has no kernels")

            # Get resource policy and idle timeout
            # In production, this would come from database lookups
            idle_timeout = 600  # Default timeout in seconds
            if hasattr(self, "_repository") and hasattr(self._repository, "_db_source"):
                # Would need proper resource policy lookup
                pass

            # Setup network configuration
            network_setup = await self._setup_network_configuration(session)
            log.debug("ssh connection info mapping: {}", network_setup.cluster_ssh_port_mapping)

            # Setup environment variables - similar to registry.py
            # Group kernels by cluster role for replica counting
            keyfunc = lambda k: k.cluster_role
            replicas = {
                cluster_role: len(list(group_iterator))
                for cluster_role, group_iterator in groupby(
                    sorted(session.kernels, key=keyfunc),
                    key=keyfunc,
                )
            }
            environ: dict[str, str] = {
                **session.environ,
                "BACKENDAI_USER_UUID": str(session.user_uuid),
                "BACKENDAI_USER_EMAIL": session.user_email,
                "BACKENDAI_USER_NAME": session.user_name,
                "BACKENDAI_SESSION_ID": str(session.session_id),
                "BACKENDAI_SESSION_NAME": str(session.name),
                "BACKENDAI_CLUSTER_SIZE": str(len(session.kernels)),
                "BACKENDAI_CLUSTER_REPLICAS": ",".join(f"{k}:{v}" for k, v in replicas.items()),
                "BACKENDAI_CLUSTER_HOSTS": ",".join(
                    k.cluster_hostname or f"{k.cluster_role}{k.cluster_idx}"
                    for k in session.kernels
                ),
                "BACKENDAI_ACCESS_KEY": session.access_key,
                # BACKENDAI_SERVICE_PORTS are set as per-kernel env-vars.
                "BACKENDAI_PREOPEN_PORTS": (
                    ",".join(str(port) for port in session.kernels[0].preopen_ports)
                    if session.kernels and session.kernels[0].preopen_ports
                    else ""
                ),
            }

            # Group kernels by agent to minimize RPC calls
            kernels_by_agent: defaultdict[AgentId, list[KernelBindingData]] = defaultdict(list)
            for kernel in session.kernels:
                if kernel.agent_id:
                    kernels_by_agent[kernel.agent_id].append(kernel)

            # Create SSH keypair for cluster
            ssh_keypair = await self._create_cluster_ssh_keypair()

            # Convert ImageConfigData to ImageConfig format for agents
            image_configs_by_canonical: dict[str, ImageConfig] = {}
            for image_key, img_cfg in image_configs.items():
                image_config = img_cfg.to_image_config(AutoPullBehavior.DIGEST)
                image_configs_by_canonical[image_key] = image_config

            # Create kernels on each agent
            create_tasks: list[Awaitable[Any]] = []
            for agent_id, agent_kernels in kernels_by_agent.items():
                agent_client = self._agent_pool.get_agent_client(
                    agent_id, order_key=str(session.session_id)
                )

                # Prepare kernel creation configs
                kernel_ids = [str(k.kernel_id) for k in agent_kernels]
                kernel_configs: list[KernelCreationConfig] = []
                kernel_image_refs: dict[KernelId, ImageRef] = {}

                for idx, k in enumerate(agent_kernels):
                    kernel_id_str = str(k.kernel_id)
                    image_str = k.image

                    # Use resolved image config or fallback
                    if image_str not in image_configs_by_canonical:
                        # This should not happen - all images should be resolved by precondition check
                        log.error(
                            "Image {} not found in resolved configs - this indicates precondition check failed",
                            image_str,
                        )
                        raise ValueError(
                            f"Image {image_str} not found in database - session start failed"
                        )

                    kernel_image_config = image_configs_by_canonical[image_str]

                    # Use cluster configuration from kernel data
                    cluster_role = k.cluster_role
                    cluster_idx = k.cluster_idx
                    local_rank = k.local_rank
                    cluster_hostname = k.cluster_hostname or f"{cluster_role}{cluster_idx}"

                    # Build proper KernelCreationConfig matching registry.py format
                    kernel_config: KernelCreationConfig = {
                        "image": kernel_image_config,
                        "kernel_id": kernel_id_str,
                        "session_id": str(session.session_id),
                        "owner_user_id": str(session.user_uuid),
                        "owner_project_id": None,  # TODO: Implement project-owned sessions
                        "network_id": str(session.session_id),
                        "session_type": session.session_type,
                        "cluster_mode": session.cluster_mode,
                        "cluster_role": cluster_role,
                        "cluster_idx": cluster_idx,
                        "cluster_hostname": cluster_hostname,
                        "local_rank": local_rank,
                        "uid": k.uid,
                        "main_gid": k.main_gid,
                        "supplementary_gids": k.gids or [],
                        "resource_slots": k.requested_slots.to_json(),
                        "resource_opts": k.resource_opts or {},
                        "environ": {
                            **environ,
                            "BACKENDAI_KERNEL_ID": kernel_id_str,
                            "BACKENDAI_KERNEL_IMAGE": image_str,
                            "BACKENDAI_CLUSTER_ROLE": cluster_role,
                            "BACKENDAI_CLUSTER_IDX": str(cluster_idx),
                            "BACKENDAI_CLUSTER_LOCAL_RANK": str(local_rank),
                            "BACKENDAI_CLUSTER_HOST": cluster_hostname,
                            "BACKENDAI_SERVICE_PORTS": str(
                                kernel_image_config.get("labels", {}).get(
                                    "ai.backend.service-ports", ""
                                )
                            ),
                        },
                        "mounts": [
                            m.to_json() if hasattr(m, "to_json") else m for m in k.vfolder_mounts
                        ],
                        "package_directory": tuple(),
                        "idle_timeout": int(idle_timeout),
                        "bootstrap_script": k.bootstrap_script,
                        "startup_command": k.startup_command,
                        "internal_data": k.internal_data,
                        "auto_pull": kernel_image_config.get("auto_pull", AutoPullBehavior.DIGEST),
                        "preopen_ports": k.preopen_ports or [],
                        "allocated_host_ports": [],  # Will be populated by agent
                        "agent_addr": k.agent_addr or "",
                        "scaling_group": k.scaling_group,
                        "endpoint_id": None,  # For inference endpoints
                    }
                    kernel_configs.append(kernel_config)

                    # Create image ref for this kernel
                    kernel_image_refs[KernelId(k.kernel_id)] = ImageRef.from_image_str(
                        image_str,
                        project=kernel_image_config["project"],
                        registry=kernel_image_config["registry"]["name"],
                        architecture=k.architecture,
                        is_local=kernel_image_config["is_local"],
                    )

                # Create cluster info with network and SSH configuration
                cluster_info: ClusterInfo = {
                    "mode": session.cluster_mode,
                    "size": len(session.kernels),
                    "replicas": replicas,
                    "network_config": network_setup.network_config,
                    "ssh_keypair": ssh_keypair,
                    "cluster_ssh_port_mapping": network_setup.cluster_ssh_port_mapping,
                }

                # Create the kernels
                create_tasks.append(
                    agent_client.create_kernels(
                        str(session.session_id),
                        kernel_ids,
                        kernel_configs,
                        cluster_info,
                        kernel_image_refs,
                    )
                )

            if create_tasks:
                await asyncio.gather(*create_tasks, return_exceptions=True)

            log.info(log_fmt + "started", *log_args)

        except Exception as e:
            # Convert exception to error status info
            error_info = convert_to_status_data(e, self._config_provider.config.debug.enabled)
            log.warning(log_fmt + "failed-starting", *log_args, exc_info=True)
            # Update error info in status_data without changing status
            # Session will be retried by retry_creating_sessions later
            await self._repository.update_session_error_info(session.session_id, error_info)

    async def _setup_network_configuration(
        self,
        session: SessionDataForStart,
    ) -> NetworkSetup:
        """
        Setup network configuration based on session network type.

        :param session: Session data containing network type and configuration
        :return: NetworkSetup with network config and SSH port mapping
        """
        network_name: Optional[str] = None
        network_config: dict[str, Any] = {}
        cluster_ssh_port_mapping: Optional[ClusterSSHPortMapping] = None

        network_type = session.network_type or NetworkType.VOLATILE

        if network_type == NetworkType.PERSISTENT:
            # For persistent networks, use pre-created network
            if session.network_id:
                # In production, would look up network details from database
                network_name = f"persistent-{session.network_id}"
                network_config = {"mode": "bridge", "network_name": network_name}
        elif network_type == NetworkType.VOLATILE:
            if session.cluster_mode == ClusterMode.SINGLE_NODE and len(session.kernels) > 1:
                # Create single-node network for multi-kernel sessions
                network_name = f"bai-singlenode-{session.session_id}"
                first_kernel = session.kernels[0]
                if not first_kernel.agent_id:
                    raise ValueError(f"No agent assigned for kernel {first_kernel.kernel_id}")
                agent_client = self._agent_pool.get_agent_client(
                    first_kernel.agent_id, order_key=str(session.session_id)
                )
                try:
                    await agent_client.create_local_network(network_name)
                except Exception:
                    log.exception(f"Failed to create agent-local network {network_name}")
                    raise
                network_config = {
                    "mode": "bridge",
                    "network_name": network_name,
                }
            elif session.cluster_mode == ClusterMode.MULTI_NODE:
                # Create overlay network for multi-node sessions
                driver = self._config_provider.config.network.inter_container.default_driver
                if driver is None:
                    raise ValueError("No inter-container network driver is configured.")

                # Check if plugin is available
                if driver not in self._network_plugin_ctx.plugins:
                    available_plugins = list(self._network_plugin_ctx.plugins.keys())
                    log.error(
                        f"Network plugin '{driver}' not found. Available plugins: {available_plugins}. "
                        f"For overlay networks, ensure Docker Swarm is initialized with 'docker swarm init'."
                    )
                    raise KeyError(
                        f"Network plugin '{driver}' not found. Available plugins: {available_plugins}. "
                        f"For overlay networks, ensure Docker Swarm is initialized with 'docker swarm init'."
                    )

                network_plugin = self._network_plugin_ctx.plugins[driver]
                try:
                    network_info = await network_plugin.create_network(
                        identifier=str(session.session_id)
                    )
                    network_config = dict(network_info.options)
                    network_name = network_info.network_id
                except Exception:
                    log.exception(
                        f"Failed to create the inter-container network (plugin: {driver})"
                    )
                    raise
        elif network_type == NetworkType.HOST:
            network_config = {"mode": "host"}
            network_name = "host"

            # Setup SSH port mapping for multi-kernel sessions in host mode
            if len(session.kernels) > 1:
                port_mapping: dict[str, tuple[str, int]] = {}
                for kernel in session.kernels:
                    if not kernel.agent_id:
                        log.warning(
                            f"No agent assigned for kernel {kernel.kernel_id}, skipping port mapping"
                        )
                        continue
                    agent_client = self._agent_pool.get_agent_client(
                        kernel.agent_id, order_key=str(session.session_id)
                    )
                    port = await agent_client.assign_port()
                    # Extract host from agent_addr
                    agent_addr = kernel.agent_addr or ""
                    agent_host = (
                        agent_addr.replace("tcp://", "").split(":", maxsplit=1)[0]
                        if agent_addr
                        else "localhost"
                    )
                    cluster_hostname = f"node-{kernel.kernel_id}"
                    port_mapping[cluster_hostname] = (agent_host, port)
                cluster_ssh_port_mapping = ClusterSSHPortMapping(port_mapping)

        await self._repository.update_session_network_id(
            session.session_id,
            network_name,
        )
        return NetworkSetup(
            network_name=network_name,
            network_config=network_config,
            cluster_ssh_port_mapping=cluster_ssh_port_mapping,
        )

    async def _create_cluster_ssh_keypair(self) -> ClusterSSHKeyPair:
        """
        Create SSH keypair for cluster communication.
        Generates actual RSA SSH keys using cryptography library.

        :return: ClusterSSHKeyPair with 'public_key' and 'private_key'
        """
        key = rsa.generate_private_key(
            backend=default_backend(),
            public_exponent=65537,
            key_size=2048,
        )
        public_key = key.public_key().public_bytes(
            serialization.Encoding.OpenSSH,
            serialization.PublicFormat.OpenSSH,
        )
        public_key += b" work@cluster.backend.ai.local"
        pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
        return ClusterSSHKeyPair(
            private_key=pem.decode("utf-8"),
            public_key=public_key.decode("utf-8"),
        )

    def _filter_stuck_sessions_for_pull(
        self,
        sessions: list[SessionDataForPull],
        threshold: float,
    ) -> list[SessionDataForPull]:
        """
        Filter sessions that appear stuck based on kernel status change time.

        :param sessions: List of sessions to filter
        :param threshold: Time threshold in seconds
        :return: List of stuck sessions
        """
        current_time = time.time()
        stuck_sessions: list[SessionDataForPull] = []

        for session in sessions:
            # Check the oldest kernel's status_changed time
            oldest_status_change = min(
                (kernel.status_changed for kernel in session.kernels if kernel.status_changed),
                default=None,
            )

            if oldest_status_change is None:
                # No status change info, consider it stuck
                stuck_sessions.append(session)
            elif (current_time - oldest_status_change) >= threshold:
                # Status hasn't changed for too long
                stuck_sessions.append(session)

        return stuck_sessions

    async def _check_truly_stuck_pulling_sessions(
        self,
        sessions: list[SessionDataForPull],
        image_configs: dict[str, ImageConfigData],
    ) -> list[SessionDataForPull]:
        """
        Check if sessions are truly stuck by verifying if pulling is still in progress.

        :param sessions: List of potentially stuck sessions
        :param image_configs: Image configurations
        :return: List of sessions that are truly stuck
        """
        truly_stuck_sessions: list[SessionDataForPull] = []

        # Group images by agent to check pulling status
        agent_images: defaultdict[AgentId, set[str]] = defaultdict(set)
        session_images: dict[SessionId, set[str]] = {}

        for session in sessions:
            session_image_set = set()
            for kernel in session.kernels:
                if kernel.agent_id and kernel.image in image_configs:
                    img_cfg = image_configs[kernel.image]
                    canonical = img_cfg.canonical
                    agent_images[kernel.agent_id].add(canonical)
                    session_image_set.add(canonical)
            session_images[session.session_id] = session_image_set

        # Check pulling status for each agent
        agent_pulling_status: dict[AgentId, dict[str, bool]] = {}
        for agent_id, images in agent_images.items():
            agent_client = self._agent_pool.get_agent_client(agent_id)
            pulling_status = {}
            for image in images:
                try:
                    is_pulling = await agent_client.check_pulling(image)
                    pulling_status[image] = is_pulling
                except Exception as e:
                    log.warning(
                        "Failed to check pulling status for image {} on agent {}: {}",
                        image,
                        agent_id,
                        e,
                    )
                    # If we can't check, assume it's stuck
                    pulling_status[image] = False
            agent_pulling_status[agent_id] = pulling_status

        # Determine truly stuck sessions
        for session in sessions:
            images_to_check = session_images[session.session_id]
            if not images_to_check:
                # No images to check, consider it stuck
                truly_stuck_sessions.append(session)
                continue

            # Check if any image for this session is actively being pulled
            any_pulling = False
            for kernel in session.kernels:
                if kernel.agent_id and kernel.image in image_configs:
                    img_cfg = image_configs[kernel.image]
                    canonical = img_cfg.canonical
                    if agent_pulling_status.get(kernel.agent_id, {}).get(canonical, False):
                        any_pulling = True
                        break

            if not any_pulling:
                # No images are being pulled, session is truly stuck
                truly_stuck_sessions.append(session)

        return truly_stuck_sessions

    async def retry_preparing_sessions(self) -> ScheduleResult:
        """
        Retry PREPARING/PULLING sessions that appear stuck.
        Re-triggers check_and_pull operations for their images.

        :return: ScheduleResult with number of sessions retried
        """
        PREPARING_CHECK_THRESHOLD = 10.0  # 10 seconds

        # Get sessions with PREPARING and PULLING statuses
        sessions_with_images = await self._repository.get_sessions_for_pull(
            [
                SessionStatus.PREPARING,
                SessionStatus.PULLING,
            ],
            [
                KernelStatus.SCHEDULED,
                KernelStatus.PREPARING,
                KernelStatus.PULLING,
            ],
        )
        sessions = sessions_with_images.sessions
        image_configs = sessions_with_images.image_configs

        if not sessions:
            log.trace("No sessions found with PREPARING/PULLING status")
            return ScheduleResult()

        # Filter sessions that haven't changed status for threshold time
        stuck_sessions = self._filter_stuck_sessions_for_pull(sessions, PREPARING_CHECK_THRESHOLD)

        if not stuck_sessions:
            return ScheduleResult()

        # Check which sessions are actually stuck (not actively pulling)
        truly_stuck_sessions = await self._check_truly_stuck_pulling_sessions(
            stuck_sessions, image_configs
        )

        if not truly_stuck_sessions:
            log.debug("All sessions are actively pulling, no retry needed")
            return ScheduleResult()

        log.info("Retrying {} truly stuck PREPARING/PULLING sessions", len(truly_stuck_sessions))

        # Update retry counts and get sessions that should continue retrying
        stuck_session_ids = [session.session_id for session in truly_stuck_sessions]
        sessions_to_retry_ids = await self._repository.batch_update_stuck_session_retries(
            stuck_session_ids, SERVICE_MAX_RETRIES
        )

        if not sessions_to_retry_ids:
            log.info("All stuck sessions exceeded max retries, moved to PENDING")
            return ScheduleResult()

        # Filter sessions that should be retried based on returned IDs
        sessions_to_retry = [
            session
            for session in truly_stuck_sessions
            if session.session_id in sessions_to_retry_ids
        ]

        # Use the existing _trigger_image_pulling_for_sessions method
        await self._trigger_image_pulling_for_sessions(sessions_to_retry, image_configs)

        # Convert retried sessions to ScheduledSessionData format
        scheduled_data = [
            ScheduledSessionData(
                session_id=session.session_id,
                creation_id=session.creation_id,
                access_key=session.access_key,
                reason="triggered-by-scheduler",
            )
            for session in sessions_to_retry
        ]
        return ScheduleResult(scheduled_sessions=scheduled_data)

    def _filter_stuck_sessions_for_start(
        self,
        sessions: list[SessionDataForStart],
        threshold: float,
    ) -> list[SessionDataForStart]:
        """
        Filter sessions that appear stuck based on kernel status change time.

        :param sessions: List of sessions to filter
        :param threshold: Time threshold in seconds
        :return: List of stuck sessions
        """
        current_time = time.time()
        stuck_sessions: list[SessionDataForStart] = []

        for session in sessions:
            # Check the oldest kernel's status_changed time
            oldest_status_change = min(
                (kernel.status_changed for kernel in session.kernels if kernel.status_changed),
                default=None,
            )

            if oldest_status_change is None:
                # No status change info, consider it stuck
                stuck_sessions.append(session)
            elif (current_time - oldest_status_change) >= threshold:
                # Status hasn't changed for too long
                stuck_sessions.append(session)

        return stuck_sessions

    async def _check_truly_stuck_creating_sessions(
        self,
        sessions: list[SessionDataForStart],
    ) -> list[SessionDataForStart]:
        """
        Check if sessions are truly stuck by verifying if kernels are being created or already exist.

        :param sessions: List of potentially stuck sessions
        :return: List of sessions that are truly stuck
        """
        truly_stuck_sessions: list[SessionDataForStart] = []

        for session in sessions:
            # Check each kernel in the session
            any_active = False
            for kernel in session.kernels:
                if kernel.agent_id:
                    agent_client = self._agent_pool.get_agent_client(kernel.agent_id)
                    try:
                        # Check if kernel is being created or already exists
                        is_active = await agent_client.check_creating(str(kernel.kernel_id))
                        if is_active:
                            any_active = True
                            break
                    except Exception as e:
                        log.warning(
                            "Failed to check creating status for kernel {} on agent {}: {}",
                            kernel.kernel_id,
                            kernel.agent_id,
                            e,
                        )
                        # If we can't check, assume it's stuck

            if not any_active:
                # No kernels are being created or existing, session is truly stuck
                truly_stuck_sessions.append(session)

        return truly_stuck_sessions

    async def retry_creating_sessions(self) -> ScheduleResult:
        """
        Retry CREATING sessions that appear stuck.
        Re-triggers kernel creation operations directly.

        :return: ScheduleResult with number of sessions retried
        """
        CREATING_CHECK_THRESHOLD = 10.0  # 10 seconds

        # Get CREATING sessions from repository
        sessions_with_images = await self._repository.get_sessions_for_start(
            [SessionStatus.CREATING],
            [
                KernelStatus.PREPARED,
                KernelStatus.CREATING,
            ],
        )
        sessions = sessions_with_images.sessions
        image_configs = sessions_with_images.image_configs

        if not sessions:
            return ScheduleResult()

        # Filter sessions that haven't changed status for threshold time
        stuck_sessions = self._filter_stuck_sessions_for_start(sessions, CREATING_CHECK_THRESHOLD)

        if not stuck_sessions:
            return ScheduleResult()

        # Check which sessions are truly stuck (not actively creating)
        truly_stuck_sessions = await self._check_truly_stuck_creating_sessions(stuck_sessions)

        if not truly_stuck_sessions:
            log.debug("All sessions are actively creating kernels, no retry needed")
            return ScheduleResult()

        log.info("Retrying {} truly stuck CREATING sessions", len(truly_stuck_sessions))

        # Update retry counts and get sessions that should continue retrying
        stuck_session_ids = [session.session_id for session in truly_stuck_sessions]
        sessions_to_retry_ids = await self._repository.batch_update_stuck_session_retries(
            stuck_session_ids, SERVICE_MAX_RETRIES
        )

        if not sessions_to_retry_ids:
            log.info("All stuck sessions exceeded max retries, moved to PENDING")
            return ScheduleResult()

        # Filter sessions that should be retried based on returned IDs
        sessions_to_retry = [
            session
            for session in truly_stuck_sessions
            if session.session_id in sessions_to_retry_ids
        ]

        # Use the existing _start_sessions_concurrently method to retry
        # This will re-trigger kernel creation for stuck sessions
        await self._start_sessions_concurrently(sessions_to_retry, image_configs)

        # Convert retried sessions to ScheduledSessionData format
        scheduled_data = [
            ScheduledSessionData(
                session_id=session.session_id,
                creation_id=session.creation_id,
                access_key=session.access_key,
                reason="triggered-by-scheduler",
            )
            for session in sessions_to_retry
        ]
        return ScheduleResult(scheduled_sessions=scheduled_data)
