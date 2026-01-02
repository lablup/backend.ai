from __future__ import annotations

import asyncio
import signal
from decimal import Decimal
from typing import TYPE_CHECKING, Mapping, Optional, Sequence

import aiotools

from ai.backend.agent.agent import AbstractAgent, AgentClass
from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.agent.errors import AgentIdNotFoundError
from ai.backend.agent.etcd import AgentEtcdClientView
from ai.backend.agent.kernel import KernelRegistry
from ai.backend.agent.monitor import AgentErrorPluginContext, AgentStatsPluginContext
from ai.backend.agent.resources import ComputerContext, ResourceAllocator
from ai.backend.agent.types import AgentBackend, get_agent_discovery
from ai.backend.common.auth import PublicKey
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.metrics.types import UTILIZATION_METRIC_INTERVAL
from ai.backend.common.types import AgentId, DeviceName, SlotName

if TYPE_CHECKING:
    from .docker.metadata.server import MetadataServer


class AgentRuntime:
    _local_config: AgentUnifiedConfig
    _etcd_views: Mapping[AgentId, AgentEtcdClientView]
    _agents: Mapping[AgentId, AbstractAgent]
    _primary_agent: AbstractAgent
    _kernel_registry: KernelRegistry
    _resource_allocator: ResourceAllocator
    _metadata_server: Optional[MetadataServer]

    _stop_signal: signal.Signals
    _timer_tasks: Sequence[asyncio.Task[None]]

    @classmethod
    async def create_runtime(
        cls,
        local_config: AgentUnifiedConfig,
        etcd: AsyncEtcd,
        stats_monitor: AgentStatsPluginContext,
        error_monitor: AgentErrorPluginContext,
        agent_public_key: Optional[PublicKey],
    ) -> AgentRuntime:
        kernel_registry = KernelRegistry()
        resource_allocator = await ResourceAllocator.new(local_config, etcd)

        if local_config.agent_common.backend == AgentBackend.DOCKER:
            metadata_server = await cls._create_metadata_server(local_config, etcd, kernel_registry)
        else:
            metadata_server = None

        agent_configs = local_config.get_agent_configs()
        etcd_views: dict[AgentId, AgentEtcdClientView] = {}
        create_agent_tasks: list[asyncio.Task] = []
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
                    )
                )
                create_agent_tasks.append(create_agent_task)
        agents_list = [task.result() for task in create_agent_tasks]
        primary_agent = agents_list[0]
        agents = {agent.id: agent for agent in agents_list}

        return AgentRuntime(
            local_config=local_config,
            etcd_views=etcd_views,
            agents=agents,
            primary_agent=primary_agent,
            kernel_registry=kernel_registry,
            resource_allocator=resource_allocator,
            metadata_server=metadata_server,
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
        agent_public_key: Optional[PublicKey],
        computers: Mapping[DeviceName, ComputerContext],
        slots: Mapping[SlotName, Decimal],
        agent_class: AgentClass,
    ) -> AbstractAgent:
        agent_kwargs = {
            "kernel_registry": kernel_registry,
            "stats_monitor": stats_monitor,
            "error_monitor": error_monitor,
            "agent_public_key": agent_public_key,
            "computers": computers,
            "slots": slots,
            "agent_class": agent_class,
        }

        backend = local_config.agent_common.backend
        agent_cls = get_agent_discovery(backend).get_agent_cls()
        return await agent_cls.new(etcd_view, agent_config, **agent_kwargs)

    def __init__(
        self,
        local_config: AgentUnifiedConfig,
        etcd_views: Mapping[AgentId, AgentEtcdClientView],
        agents: dict[AgentId, AbstractAgent],
        primary_agent: AbstractAgent,
        kernel_registry: KernelRegistry,
        resource_allocator: ResourceAllocator,
        metadata_server: Optional[MetadataServer] = None,
    ) -> None:
        self._local_config = local_config
        self._etcd_views = etcd_views
        self._agents = agents
        self._primary_agent = primary_agent
        self._kernel_registry = kernel_registry
        self._resource_allocator = resource_allocator
        self._metadata_server = metadata_server

        self._stop_signal = signal.SIGTERM
        self._timer_tasks = [
            aiotools.create_timer(self._update_slots, 30.0),
            aiotools.create_timer(self._collect_node_stat, UTILIZATION_METRIC_INTERVAL),
        ]

    async def __aexit__(self, *exc_info) -> None:
        await aiotools.cancel_and_wait(self._timer_tasks)
        for agent in self._agents.values():
            await agent.shutdown(self._stop_signal)
        if self._metadata_server is not None:
            await self._metadata_server.cleanup()
        await self._resource_allocator.__aexit__(*exc_info)

    def get_agents(self) -> list[AbstractAgent]:
        return list(self._agents.values())

    def get_agent(self, agent_id: Optional[AgentId]) -> AbstractAgent:
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

    async def _update_slots(self, interval: float) -> None:
        for agent_id, agent in self._agents.items():
            updated_slots = await self._resource_allocator.get_updated_slots(agent_id)
            agent.update_slots(updated_slots)

    async def _collect_node_stat(self, interval: float) -> None:
        for agent_id, agent in self._agents.items():
            await agent.collect_node_stat(
                self._resource_allocator.get_resource_scaling_factor(agent_id)
            )
