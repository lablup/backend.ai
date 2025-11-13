import asyncio
import importlib
import signal
from typing import TYPE_CHECKING, Optional, Type

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
from ai.backend.common.types import AgentId, aobject

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


class AgentRuntime(aobject):
    local_config: AgentUnifiedConfig
    agents: dict[AgentId, AbstractAgent]
    kernel_registry: KernelRegistry
    etcd: AsyncEtcd
    etcd_views: dict[AgentId, AgentEtcdClientView]

    _default_agent_id: AgentId
    _stop_signal: signal.Signals

    def __init__(
        self,
        local_config: AgentUnifiedConfig,
        etcd: AsyncEtcd,
        stats_monitor: AgentStatsPluginContext,
        error_monitor: AgentErrorPluginContext,
        agent_public_key: Optional[PublicKey],
    ) -> None:
        self.local_config = local_config
        self.agents = {}
        self.kernel_registry = KernelRegistry()
        self.etcd = etcd
        self.etcd_views = {}
        self.metadata_server: MetadataServer | None = None

        agent_configs = self.local_config.get_agent_configs()
        self._default_agent_id = AgentId(agent_configs[0].agent.id)
        self._stop_signal = signal.SIGTERM

        self.stats_monitor = stats_monitor
        self.error_monitor = error_monitor
        self.agent_public_key = agent_public_key

    async def __ainit__(self) -> None:
        if self.local_config.agent_common.backend == AgentBackend.DOCKER:
            await self._initialize_metadata_server()

        tasks = []
        async with asyncio.TaskGroup() as tg:
            for agent_config in self.local_config.get_agent_configs():
                agent_id = AgentId(agent_config.agent.id)
                etcd_view = AgentEtcdClientView(self.etcd, agent_config)

                self.etcd_views[agent_id] = etcd_view
                tasks.append(tg.create_task(self._create_agent(etcd_view, agent_config)))
        self.agents = {(agent := task.result()).id: agent for task in tasks}

    async def __aexit__(self, *exc_info) -> None:
        for agent in self.agents.values():
            await agent.shutdown(self._stop_signal)
        if self.metadata_server is not None:
            await self.metadata_server.cleanup()

    def get_agents(self) -> list[AbstractAgent]:
        return list(self.agents.values())

    def get_agent(self, agent_id: Optional[AgentId]) -> AbstractAgent:
        if agent_id is None:
            agent_id = self._default_agent_id
        if agent_id not in self.agents:
            raise AgentIdNotFoundError(
                f"Agent '{agent_id}' not found in this runtime. "
                f"Available agents: {', '.join(self.agents.keys())}"
            )
        return self.agents[agent_id]

    def get_etcd(self, agent_id: Optional[AgentId]) -> AgentEtcdClientView:
        if agent_id is None:
            agent_id = self._default_agent_id
        if agent_id not in self.agents:
            raise AgentIdNotFoundError(
                f"Agent '{agent_id}' not found in this runtime. "
                f"Available agents: {', '.join(self.agents.keys())}"
            )
        return self.etcd_views[agent_id]

    def mark_stop_signal(self, stop_signal: signal.Signals) -> None:
        self._stop_signal = stop_signal

    async def update_status(self, status, agent_id: AgentId) -> None:
        etcd = self.get_etcd(agent_id)
        await etcd.put("", status, scope=ConfigScopes.NODE)

    async def _create_agent(
        self,
        etcd_view: AgentEtcdClientView,
        agent_config: AgentUnifiedConfig,
    ) -> AbstractAgent:
        agent_kwargs = {
            "kernel_registry": self.kernel_registry,
            "stats_monitor": self.stats_monitor,
            "error_monitor": self.error_monitor,
            "agent_public_key": self.agent_public_key,
        }

        backend = self.local_config.agent_common.backend
        agent_mod = importlib.import_module(f"ai.backend.agent.{backend.value}")
        agent_cls: Type[AbstractAgent] = agent_mod.get_agent_cls()

        return await agent_cls.new(etcd_view, agent_config, **agent_kwargs)

    async def _initialize_metadata_server(self) -> None:
        from .docker.metadata.server import MetadataServer

        self.metadata_server = await MetadataServer.new(
            self.local_config,
            self.etcd,
            kernel_registry=self.kernel_registry.global_view(),
        )
        await self.metadata_server.start_server()
