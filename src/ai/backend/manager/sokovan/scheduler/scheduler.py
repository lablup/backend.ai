from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.types import ResourceSlot, SessionId
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.clients.agent import AgentPool
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.metrics.scheduler import SchedulerPhaseMetricObserver
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.repositories.scheduler import SchedulerRepository
from ai.backend.manager.types import DistributedLockFactory

from .hooks.registry import HookRegistry, HookRegistryArgs
from .launcher.launcher import SessionLauncher
from .provisioner.provisioner import SessionProvisioner
from .results import ScheduledSessionData, ScheduleResult
from .terminator.terminator import SessionTerminator
from .types import SessionRunningData

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class SchedulerArgs:
    provisioner: SessionProvisioner
    launcher: SessionLauncher
    terminator: SessionTerminator
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
    _terminator: SessionTerminator
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
        self._terminator = args.terminator
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
        Delegates to SessionTerminator for the actual termination logic.

        Returns:
            ScheduleResult from the termination operation.
        """
        return await self._terminator.terminate_sessions()

    async def sweep_stale_sessions(self) -> ScheduleResult:
        """
        Sweep stale sessions including those with pending timeout.
        Delegates to SessionTerminator for the actual sweep logic.

        Returns:
            ScheduleResult with the count of swept sessions.
        """
        return await self._terminator.sweep_stale_sessions()

    async def sweep_lost_agent_kernels(self) -> ScheduleResult:
        """
        Sweep kernels in TERMINATING sessions that cannot be terminated normally.
        Delegates to SessionTerminator for the actual sweep logic.

        Returns:
            ScheduleResult (empty - no scheduled sessions).
        """
        return await self._terminator.sweep_lost_agent_kernels()

    async def sweep_stale_kernels(self) -> ScheduleResult:
        """
        Sweep kernels with stale presence status.
        Delegates to SessionTerminator for the actual sweep logic.

        Returns:
            ScheduleResult with affected sessions for post-processing.
        """
        return await self._terminator.sweep_stale_kernels()

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
