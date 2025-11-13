import asyncio
import importlib
import signal
from typing import TYPE_CHECKING, Mapping, Optional, Type

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.agent.etcd import AgentEtcdClientView
from ai.backend.agent.kernel import KernelRegistry
from ai.backend.agent.monitor import AgentErrorPluginContext, AgentStatsPluginContext
from ai.backend.agent.types import AgentBackend
from ai.backend.common.auth import PublicKey
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.common.types import AgentId

if TYPE_CHECKING:
    from .docker.metadata.server import MetadataServer


class AgentIdNotFoundError(BackendAIError):
    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class AgentRuntime:
    _local_config: AgentUnifiedConfig
    _agents: dict[AgentId, AbstractAgent]
    _default_agent: AbstractAgent
    _kernel_registry: KernelRegistry
    _etcd: AsyncEtcd
    _etcd_views: Mapping[AgentId, AgentEtcdClientView]

    _stop_signal: signal.Signals

    def __init__(
        self,
        local_config: AgentUnifiedConfig,
        etcd: AsyncEtcd,
    ) -> None:
        self._local_config = local_config
        self._agents = {}
        self._kernel_registry = KernelRegistry()
        self._etcd = etcd
        self._etcd_views = {
            AgentId(agent_config.agent.id): AgentEtcdClientView(self._etcd, agent_config)
            for agent_config in self._local_config.get_agent_configs()
        }
        self._metadata_server: MetadataServer | None = None

        self._stop_signal = signal.SIGTERM

    async def create_agents(
        self,
        stats_monitor: AgentStatsPluginContext,
        error_monitor: AgentErrorPluginContext,
        agent_public_key: Optional[PublicKey],
    ) -> None:
        if self._local_config.agent_common.backend == AgentBackend.DOCKER:
            await self._initialize_metadata_server()

        tasks: list[asyncio.Task] = []
        async with asyncio.TaskGroup() as tg:
            for agent_config in self._local_config.get_agent_configs():
                agent_id = AgentId(agent_config.agent.id)
                tasks.append(
                    tg.create_task(
                        self._create_agent(
                            self.get_etcd(agent_id),
                            agent_config,
                            stats_monitor,
                            error_monitor,
                            agent_public_key,
                        )
                    )
                )

        agents = [task.result() for task in tasks]
        self._default_agent = agents[0]
        self._agents = {agent.id: agent for agent in agents}

    async def __aexit__(self, *exc_info) -> None:
        for agent in self._agents.values():
            await agent.shutdown(self._stop_signal)
        if self._metadata_server is not None:
            await self._metadata_server.cleanup()

    def get_agents(self) -> list[AbstractAgent]:
        return list(self._agents.values())

    def get_agent(self, agent_id: Optional[AgentId]) -> AbstractAgent:
        if agent_id is None:
            return self._default_agent
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

    async def update_status(self, status, agent_id: AgentId) -> None:
        etcd = self.get_etcd(agent_id)
        await etcd.put("", status, scope=ConfigScopes.NODE)

    async def _create_agent(
        self,
        etcd_view: AgentEtcdClientView,
        agent_config: AgentUnifiedConfig,
        stats_monitor: AgentStatsPluginContext,
        error_monitor: AgentErrorPluginContext,
        agent_public_key: Optional[PublicKey],
    ) -> AbstractAgent:
        agent_kwargs = {
            "kernel_registry": self._kernel_registry,
            "stats_monitor": stats_monitor,
            "error_monitor": error_monitor,
            "agent_public_key": agent_public_key,
        }

        backend = self._local_config.agent_common.backend
        agent_mod = importlib.import_module(f"ai.backend.agent.{backend.value}")
        agent_cls: Type[AbstractAgent] = agent_mod.get_agent_cls()

        return await agent_cls.new(etcd_view, agent_config, **agent_kwargs)

    async def _initialize_metadata_server(self) -> None:
        from .docker.metadata.server import MetadataServer

        self._metadata_server = await MetadataServer.new(
            self._local_config,
            self._etcd,
            kernel_registry=self._kernel_registry.global_view(),
        )
        await self._metadata_server.start_server()
