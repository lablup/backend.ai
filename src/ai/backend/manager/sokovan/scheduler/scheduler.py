from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Awaitable, Optional
from uuid import UUID

from ai.backend.common.clients.valkey_client.valkey_schedule import HealthCheckStatus
from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.types import (
    AgentId,
    KernelId,
    ResourceSlot,
    SessionId,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.clients.agent import AgentPool
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.metrics.scheduler import (
    SchedulerPhaseMetricObserver,
)
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.repositories.scheduler import (
    KernelTerminationResult,
    SchedulerRepository,
    TerminatingKernelData,
)
from ai.backend.manager.scheduler.types import ScheduleType
from ai.backend.manager.types import DistributedLockFactory

from .hooks.registry import HookRegistry, HookRegistryArgs
from .launcher.launcher import SessionLauncher
from .provisioner.provisioner import SessionProvisioner
from .results import ScheduledSessionData, ScheduleResult
from .types import (
    SessionRunningData,
    SessionTransitionData,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class AgentTerminationGroup:
    """Groups kernels by agent for batch termination."""

    agent_id: Optional[AgentId]
    agent_addr: Optional[str]
    kernels: list[TerminatingKernelData] = field(default_factory=list)


@dataclass
class SchedulerArgs:
    provisioner: SessionProvisioner
    launcher: SessionLauncher
    repository: SchedulerRepository
    deployment_repository: DeploymentRepository
    config_provider: ManagerConfigProvider
    lock_factory: DistributedLockFactory
    agent_pool: AgentPool
    network_plugin_ctx: NetworkPluginContext
    event_producer: EventProducer
    valkey_schedule: ValkeyScheduleClient


class Scheduler:
    _provisioner: SessionProvisioner
    _launcher: SessionLauncher
    _repository: SchedulerRepository
    _config_provider: ManagerConfigProvider
    _lock_factory: DistributedLockFactory
    _agent_pool: AgentPool
    _network_plugin_ctx: NetworkPluginContext
    _phase_metrics: SchedulerPhaseMetricObserver
    _hook_registry: HookRegistry
    _valkey_schedule: ValkeyScheduleClient  # TODO: Remove this client and use only via repository

    def __init__(self, args: SchedulerArgs) -> None:
        self._provisioner = args.provisioner
        self._launcher = args.launcher
        self._repository = args.repository
        self._config_provider = args.config_provider
        self._lock_factory = args.lock_factory
        self._agent_pool = args.agent_pool
        self._network_plugin_ctx = args.network_plugin_ctx
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

    async def schedule_all_scaling_groups(self) -> ScheduleResult:
        """
        Schedule sessions for all scaling groups.
        Delegates to SessionProvisioner for the actual scheduling logic.

        Returns:
            ScheduleResult: Result of the scheduling operation.
        """
        all_scheduled_sessions: list[ScheduledSessionData] = []
        # Get all schedulable scaling groups from repository
        scaling_groups = await self._repository.get_schedulable_scaling_groups()
        for scaling_group in scaling_groups:
            try:
                log.trace("Scheduling sessions for scaling group: {}", scaling_group)
                # Schedule sessions for this scaling group via provisioner
                with self._phase_metrics.measure_phase("scheduler", scaling_group, "scheduling"):
                    scheduled_result = await self._provisioner.schedule_scaling_group(scaling_group)
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

    async def sweep_stale_kernels(self) -> ScheduleResult:
        """
        Sweep kernels with stale presence status.
        Only updates kernel status to TERMINATED, does NOT change session status.

        :return: ScheduleResult with affected sessions for post-processing
        """
        # 1. Get RUNNING sessions with RUNNING kernels
        running_sessions = await self._repository.get_sessions_for_transition(
            session_statuses=[SessionStatus.RUNNING],
            kernel_statuses=[KernelStatus.RUNNING],
        )
        if not running_sessions:
            return ScheduleResult()

        # 2. Extract kernel IDs and agent IDs, then check presence status in Redis
        running_kernel_ids: list[KernelId] = []
        agent_ids: set[AgentId] = set()
        for session in running_sessions:
            for kernel in session.kernels:
                running_kernel_ids.append(KernelId(UUID(kernel.kernel_id)))
                agent_ids.add(kernel.agent_id)
        statuses = await self._valkey_schedule.check_kernel_presence_status_batch(
            running_kernel_ids,
            agent_ids=agent_ids,
        )

        # 3. Filter STALE kernels (None status or STALE presence)
        stale_kernel_id_set: set[str] = {
            str(kernel_id)
            for kernel_id in running_kernel_ids
            if (status := statuses.get(kernel_id)) is None
            or status.presence == HealthCheckStatus.STALE
        }
        if not stale_kernel_id_set:
            return ScheduleResult()

        # 4. Check with agent RPC - only explicit False terminates
        dead_kernel_ids: list[str] = []
        affected_sessions: list[SessionTransitionData] = []

        for session in running_sessions:
            for kernel in session.kernels:
                if kernel.kernel_id not in stale_kernel_id_set:
                    continue
                try:
                    agent_client = self._agent_pool.get_agent_client(kernel.agent_id)
                    is_running = await agent_client.check_running(kernel.kernel_id)
                    if is_running is False:
                        dead_kernel_ids.append(kernel.kernel_id)
                        if session not in affected_sessions:
                            affected_sessions.append(session)
                except Exception as e:
                    log.warning(
                        "Failed to check kernel {} status: {}. Skipping.",
                        kernel.kernel_id,
                        e,
                    )

        if not dead_kernel_ids:
            return ScheduleResult()

        # 5. Update kernel status to TERMINATED (NOT session status)
        updated_count = await self._repository.update_kernels_to_terminated(
            dead_kernel_ids, reason="STALE_KERNEL"
        )
        log.info("Marked {} stale kernels as TERMINATED", updated_count)

        # 6. Return result for post_process to trigger CHECK_RUNNING_SESSION_TERMINATION
        return ScheduleResult(
            scheduled_sessions=[
                ScheduledSessionData(
                    session_id=s.session_id,
                    creation_id=s.creation_id,
                    access_key=s.access_key,
                    reason="STALE_KERNEL",
                )
                for s in affected_sessions
            ]
        )

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

        Delegates to SessionLauncher.

        :return: ScheduleResult with the count of sessions transitioned
        """
        return await self._launcher.check_preconditions()

    async def start_sessions(self) -> ScheduleResult:
        """
        Start sessions that have passed precondition checks.
        Transitions sessions from PREPARED to CREATING and starts kernels on agents.

        Delegates to SessionLauncher for the actual execution.

        :return: ScheduleResult with the count of sessions started
        """
        return await self._launcher.start_sessions()

    async def retry_preparing_sessions(self) -> ScheduleResult:
        """
        Retry PREPARING/PULLING sessions that appear stuck.
        Re-triggers check_and_pull operations for their images.

        Delegates to SessionLauncher for the actual execution.

        :return: ScheduleResult with number of sessions retried
        """
        return await self._launcher.retry_preparing_sessions()

    async def retry_creating_sessions(self) -> ScheduleResult:
        """
        Retry CREATING sessions that appear stuck.
        Re-triggers kernel creation operations directly.

        Delegates to SessionLauncher for the actual execution.

        :return: ScheduleResult with number of sessions retried
        """
        return await self._launcher.retry_creating_sessions()

    async def check_running_session_termination(self) -> ScheduleResult:
        """
        Check RUNNING sessions where all kernels are TERMINATED and mark them as TERMINATING.

        :return: ScheduleResult with sessions marked as TERMINATING
        """
        # Get RUNNING sessions where ALL kernels are TERMINATED
        sessions = await self._repository.get_sessions_for_transition(
            session_statuses=[SessionStatus.RUNNING],
            kernel_statuses=[KernelStatus.TERMINATED],
        )

        if not sessions:
            return ScheduleResult()

        # Mark sessions as TERMINATING
        session_ids = [s.session_id for s in sessions]
        await self._repository.mark_sessions_terminating(session_ids, reason="ABNORMAL_TERMINATION")

        log.info(
            "Marked {} RUNNING sessions as TERMINATING (all kernels terminated unexpectedly)",
            len(session_ids),
        )

        return ScheduleResult(
            scheduled_sessions=[
                ScheduledSessionData(
                    session_id=s.session_id,
                    creation_id=s.creation_id,
                    access_key=s.access_key,
                    reason="ABNORMAL_TERMINATION",
                )
                for s in sessions
            ]
        )
