from __future__ import annotations

import asyncio
import signal
from collections.abc import Mapping
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from ai.backend.agent.agent import AbstractAgent, AgentClass
from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.agent.errors import AgentIdNotFoundError
from ai.backend.agent.etcd import AgentEtcdClientView
from ai.backend.agent.kernel import KernelRegistry
from ai.backend.agent.monitor import AgentErrorPluginContext, AgentStatsPluginContext
from ai.backend.agent.resources import ComputerContext, ResourceAllocator
from ai.backend.agent.tasks import CollectNodeStatTask, UpdateSlotsTask
from ai.backend.agent.tasks.refresh_volume_status_checks import (
    RefreshVolumeStatusChecksTask,
    RefreshVolumeStatusChecksTaskArgs,
)
from ai.backend.agent.types import AgentBackend, get_agent_discovery
from ai.backend.common.auth import PublicKey
from ai.backend.common.clients.valkey_client.sentinel_monitor.monitor_set import SentinelMonitorSet
from ai.backend.common.clients.valkey_client.valkey_storage_volume.client import (
    ValkeyStorageVolumeClient,
)
from ai.backend.common.cron import LocalCron, PeriodicTask
from ai.backend.common.data.entity.storage_volume import StorageVolumeName
from ai.backend.common.defs import REDIS_STORAGE_VOLUME_DB, RedisRole
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.exception import ConfigurationError
from ai.backend.common.storage.probe.registry import VolumeStatusCheckRegistry
from ai.backend.common.storage.probe.report import (
    StorageStatusReportTask,
    StorageStatusReportTaskArgs,
)
from ai.backend.common.storage.probe.reporter import VolumeStatusReporter, VolumeStatusReporterArgs
from ai.backend.common.storage.probe.runner import ProbeCheckRunner, ProbeCheckRunnerArgs
from ai.backend.common.storage.probe.volume import AbstractVolumeStatusCheck
from ai.backend.common.types import AgentId, DeviceName, SlotName

if TYPE_CHECKING:
    from .docker.metadata.server import MetadataServer


class AgentRuntime:
    _local_config: AgentUnifiedConfig
    _etcd_views: Mapping[AgentId, AgentEtcdClientView]
    _agents: Mapping[AgentId, AbstractAgent[Any, Any]]
    _primary_agent: AbstractAgent[Any, Any]
    _kernel_registry: KernelRegistry
    _resource_allocator: ResourceAllocator
    _metadata_server: MetadataServer | None

    _stop_signal: signal.Signals
    _volume_status_check_registry: VolumeStatusCheckRegistry
    _probe_check_runner: ProbeCheckRunner[StorageVolumeName]
    _valkey_storage_volume_client: ValkeyStorageVolumeClient | None
    _refresh_volume_status_checks_task: RefreshVolumeStatusChecksTask | None
    _local_cron: LocalCron

    @classmethod
    async def create_runtime(
        cls,
        local_config: AgentUnifiedConfig,
        etcd: AsyncEtcd,
        stats_monitor: AgentStatsPluginContext,
        error_monitor: AgentErrorPluginContext,
        agent_public_key: PublicKey | None,
        sentinel_monitors: SentinelMonitorSet,
    ) -> AgentRuntime:
        kernel_registry = KernelRegistry()
        resource_allocator = await ResourceAllocator.new(local_config, etcd)

        if local_config.agent_common.backend == AgentBackend.DOCKER:
            metadata_server = await cls._create_metadata_server(local_config, etcd, kernel_registry)
        else:
            metadata_server = None

        agent_configs = local_config.get_agent_configs()
        etcd_views: dict[AgentId, AgentEtcdClientView] = {}
        create_agent_tasks: list[asyncio.Task[Any]] = []
        async with asyncio.TaskGroup() as tg:
            for i, agent_config in enumerate(agent_configs):
                agent_id = AgentId(agent_config.agent.defaulted_id)

                etcd_view = AgentEtcdClientView(etcd, agent_config)
                etcd_views[agent_id] = etcd_view

                computers = resource_allocator.get_computers(agent_id)
                slots = await resource_allocator.get_updated_slots(agent_id)
                agent_class = AgentClass.PRIMARY if i == 0 else AgentClass.AUXILIARY

                create_agent_task = tg.create_task(
                    cls._create_agent(
                        local_config,
                        etcd_view,
                        kernel_registry,
                        agent_config,
                        stats_monitor,
                        error_monitor,
                        agent_public_key,
                        computers,
                        slots,
                        agent_class,
                        sentinel_monitors,
                    )
                )
                create_agent_tasks.append(create_agent_task)
        agents_list = [task.result() for task in create_agent_tasks]
        primary_agent = agents_list[0]
        agents = {agent.id: agent for agent in agents_list}
        valkey_storage_volume_client = await cls._create_valkey_storage_volume_client(
            local_config, sentinel_monitors
        )

        runtime = AgentRuntime(
            local_config=local_config,
            etcd_views=etcd_views,
            agents=agents,
            primary_agent=primary_agent,
            kernel_registry=kernel_registry,
            resource_allocator=resource_allocator,
            metadata_server=metadata_server,
            valkey_storage_volume_client=valkey_storage_volume_client,
        )
        await runtime._local_cron.start()
        await runtime._probe_check_runner.start()
        return runtime

    @classmethod
    async def _create_valkey_storage_volume_client(
        cls,
        local_config: AgentUnifiedConfig,
        sentinel_monitors: SentinelMonitorSet,
    ) -> ValkeyStorageVolumeClient:
        if local_config.redis is None:
            raise ConfigurationError({
                "AgentRuntime.create_runtime": "Redis runtime configuration is not set."
            })
        valkey_target = (
            local_config.redis.to_redis_profile_target()
            .profile_target(RedisRole.STORAGE_VOLUME)
            .to_valkey_target()
        )
        return await ValkeyStorageVolumeClient.create(
            valkey_target,
            human_readable_name="agent.storage_volume",
            db_id=REDIS_STORAGE_VOLUME_DB,
            sentinel_monitor=sentinel_monitors.monitor_for(valkey_target),
        )

    @classmethod
    async def _create_metadata_server(
        cls,
        local_config: AgentUnifiedConfig,
        etcd: AsyncEtcd,
        kernel_registry: KernelRegistry,
    ) -> MetadataServer:
        from .docker.metadata.server import MetadataServer

        metadata_server = await MetadataServer.new(
            local_config,
            etcd,
            kernel_registry=kernel_registry.global_view(),
        )
        await metadata_server.start_server()
        return metadata_server

    @classmethod
    async def _create_agent(
        cls,
        local_config: AgentUnifiedConfig,
        etcd_view: AgentEtcdClientView,
        kernel_registry: KernelRegistry,
        agent_config: AgentUnifiedConfig,
        stats_monitor: AgentStatsPluginContext,
        error_monitor: AgentErrorPluginContext,
        agent_public_key: PublicKey | None,
        computers: Mapping[DeviceName, ComputerContext],
        slots: Mapping[SlotName, Decimal],
        agent_class: AgentClass,
        sentinel_monitors: SentinelMonitorSet,
    ) -> AbstractAgent[Any, Any]:
        agent_kwargs = {
            "kernel_registry": kernel_registry,
            "stats_monitor": stats_monitor,
            "error_monitor": error_monitor,
            "agent_public_key": agent_public_key,
            "computers": computers,
            "slots": slots,
            "agent_class": agent_class,
            "sentinel_monitors": sentinel_monitors,
        }

        backend = local_config.agent_common.backend
        agent_cls = get_agent_discovery(backend).get_agent_cls()
        return await agent_cls.new(etcd_view, agent_config, **agent_kwargs)

    def __init__(
        self,
        local_config: AgentUnifiedConfig,
        etcd_views: Mapping[AgentId, AgentEtcdClientView],
        agents: dict[AgentId, AbstractAgent[Any, Any]],
        primary_agent: AbstractAgent[Any, Any],
        kernel_registry: KernelRegistry,
        resource_allocator: ResourceAllocator,
        metadata_server: MetadataServer | None = None,
        valkey_storage_volume_client: ValkeyStorageVolumeClient | None = None,
    ) -> None:
        self._local_config = local_config
        self._etcd_views = etcd_views
        self._agents = agents
        self._primary_agent = primary_agent
        self._kernel_registry = kernel_registry
        self._resource_allocator = resource_allocator
        self._metadata_server = metadata_server
        self._valkey_storage_volume_client = valkey_storage_volume_client

        self._stop_signal = signal.SIGTERM
        volume_status_checks: list[AbstractVolumeStatusCheck] = []
        self._volume_status_check_registry = VolumeStatusCheckRegistry(volume_status_checks)
        self._probe_check_runner = ProbeCheckRunner(
            ProbeCheckRunnerArgs(checks=volume_status_checks)
        )
        periodic_tasks: list[PeriodicTask] = [
            UpdateSlotsTask(self),
            CollectNodeStatTask(self, local_config),
        ]
        self._refresh_volume_status_checks_task = None
        if valkey_storage_volume_client is not None:
            self._refresh_volume_status_checks_task = RefreshVolumeStatusChecksTask(
                RefreshVolumeStatusChecksTaskArgs(
                    valkey_storage_volume_client=valkey_storage_volume_client,
                    agent_ids=list(agents.keys()),
                    registry=self._volume_status_check_registry,
                    runner=self._probe_check_runner,
                    local_config=local_config,
                )
            )
            periodic_tasks.append(self._refresh_volume_status_checks_task)
        sd_config = local_config.service_discovery
        # The manager tells reports apart by these ids, so without both there is nothing to report.
        if sd_config.instance_id and sd_config.service_group:
            reporter = VolumeStatusReporter(
                VolumeStatusReporterArgs(
                    registry=self._volume_status_check_registry,
                    service_catalog_instance_id=sd_config.instance_id,
                    service_catalog_service_group=sd_config.service_group,
                )
            )
            periodic_tasks.append(
                StorageStatusReportTask(
                    StorageStatusReportTaskArgs(
                        reporter=reporter,
                        event_producer=primary_agent.event_producer,
                        interval=local_config.storage_status_report.interval,
                        initial_delay=local_config.storage_status_report.initial_delay,
                    )
                )
            )
        self._local_cron = LocalCron(periodic_tasks)

    async def __aexit__(self, *exc_info: Any) -> None:
        await self._local_cron.stop()
        await self._probe_check_runner.stop()
        if self._refresh_volume_status_checks_task is not None:
            await self._refresh_volume_status_checks_task.close()
        if self._valkey_storage_volume_client is not None:
            await self._valkey_storage_volume_client.close()
        for agent in self._agents.values():
            await agent.shutdown(self._stop_signal)
        if self._metadata_server is not None:
            await self._metadata_server.cleanup()
        await self._resource_allocator.__aexit__(*exc_info)

    def get_agents(self) -> list[AbstractAgent[Any, Any]]:
        return list(self._agents.values())

    def get_agent(self, agent_id: AgentId | None) -> AbstractAgent[Any, Any]:
        if agent_id is None:
            return self._primary_agent
        if agent_id not in self._agents:
            raise AgentIdNotFoundError(
                f"Agent '{agent_id}' not found in this runtime. "
                f"Available agents: {', '.join(self._agents.keys())}"
            )
        return self._agents[agent_id]

    def get_etcd(self, agent_id: AgentId) -> AgentEtcdClientView:
        if agent_id not in self._etcd_views:
            raise AgentIdNotFoundError(
                f"Etcd client for agent '{agent_id}' not found in this runtime. "
                f"Available agent etcd views: {', '.join(self._etcd_views.keys())}"
            )
        return self._etcd_views[agent_id]

    def mark_stop_signal(self, stop_signal: signal.Signals) -> None:
        self._stop_signal = stop_signal

    async def update_status(self, status: str, agent_id: AgentId) -> None:
        etcd = self.get_etcd(agent_id)
        await etcd.put("", status, scope=ConfigScopes.NODE)

    async def update_agent_slots(self) -> None:
        for agent_id, agent in self._agents.items():
            updated_slots = await self._resource_allocator.get_updated_slots(agent_id)
            agent.update_slots(updated_slots)

    async def collect_node_stats(self) -> None:
        for agent_id, agent in self._agents.items():
            await agent.collect_node_stat(
                self._resource_allocator.get_resource_scaling_factor(agent_id)
            )
