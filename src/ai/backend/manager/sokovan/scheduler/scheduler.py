from __future__ import annotations

import logging
from dataclasses import dataclass

from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.clients.agent import AgentPool
from ai.backend.manager.config.provider import ManagerConfigProvider
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

                # Fetch scheduling data for this scaling group
                scheduling_data = await self._repository.get_scheduling_data(scaling_group)
                if scheduling_data is None:
                    log.trace(
                        "No pending sessions for scaling group {}. Skipping.",
                        scaling_group,
                    )
                    continue

                # Schedule sessions for this scaling group via provisioner
                with self._phase_metrics.measure_phase("scheduler", scaling_group, "scheduling"):
                    scheduled_result = await self._provisioner.schedule_scaling_group(
                        scaling_group, scheduling_data
                    )
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
