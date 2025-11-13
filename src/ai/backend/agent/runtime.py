import importlib
import signal
from typing import Optional

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.agent.monitor import AgentErrorPluginContext, AgentStatsPluginContext
from ai.backend.common.auth import PublicKey
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.types import aobject


class AgentRuntime(aobject):
    local_config: AgentUnifiedConfig
    agent: AbstractAgent
    etcd: AsyncEtcd

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
        self.etcd = etcd

        self._stop_signal = signal.SIGTERM

        self.stats_monitor = stats_monitor
        self.error_monitor = error_monitor
        self.agent_public_key = agent_public_key

    async def __ainit__(self) -> None:
        self.agent = await self._create_agent(self.etcd, self.local_config)

    async def __aexit__(self, *exc_info) -> None:
        await self.agent.shutdown(self._stop_signal)

    def get_agent(self) -> AbstractAgent:
        return self.agent

    def get_etcd(self) -> AsyncEtcd:
        return self.etcd

    def mark_stop_signal(self, stop_signal: signal.Signals) -> None:
        self._stop_signal = stop_signal

    async def update_status(self, status) -> None:
        etcd = self.get_etcd()
        await etcd.put("", status, scope=ConfigScopes.NODE)

    async def _create_agent(
        self,
        etcd: AsyncEtcd,
        agent_config: AgentUnifiedConfig,
    ) -> AbstractAgent:
        agent_kwargs = {
            "stats_monitor": self.stats_monitor,
            "error_monitor": self.error_monitor,
            "agent_public_key": self.agent_public_key,
        }

        backend = self.local_config.agent_common.backend
        agent_mod = importlib.import_module(f"ai.backend.agent.{backend.value}")
        agent_cls = agent_mod.get_agent_cls()

        return agent_cls.new(etcd, agent_config, **agent_kwargs)
