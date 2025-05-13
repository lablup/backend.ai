import logging

import aiohttp
import sqlalchemy as sa
import yarl
from async_timeout import timeout as _timeout

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.types import (
    AgentId,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.services.agent.actions.get_watcher_status import (
    GetWatcherStatusAction,
    GetWatcherStatusActionResult,
)
from ai.backend.manager.services.agent.actions.recalculate_usage import (
    RecalculateUsageAction,
    RecalculateUsageActionResult,
)
from ai.backend.manager.services.agent.actions.sync_agent_registry import (
    SyncAgentRegistryAction,
    SyncAgentRegistryActionResult,
)
from ai.backend.manager.services.agent.actions.watcher_agent_restart import (
    WatcherAgentRestartAction,
    WatcherAgentRestartActionResult,
)
from ai.backend.manager.services.agent.actions.watcher_agent_start import (
    WatcherAgentStartAction,
    WatcherAgentStartActionResult,
)
from ai.backend.manager.services.agent.actions.watcher_agent_stop import (
    WatcherAgentStopAction,
    WatcherAgentStopActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AgentService:
    _db: ExtendedAsyncSAEngine
    _etcd: AsyncEtcd
    _config_provider: ManagerConfigProvider
    _agent_registry: AgentRegistry

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        etcd: AsyncEtcd,
        agent_registry: AgentRegistry,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._db = db
        self._etcd = etcd
        self._agent_registry = agent_registry
        self._config_provider = config_provider

    async def _get_watcher_info(self, agent_id: AgentId) -> dict:
        """
        Get watcher information.
        :return addr: address of agent watcher (eg: http://127.0.0.1:6009)
        :return token: agent watcher token ("insecure" if not set in config server)
        """
        token = self._config_provider.config.watcher.token
        if token is None:
            token = "insecure"
        agent_ip = await self._etcd.get(f"nodes/agents/{agent_id}/ip")
        raw_watcher_port = await self._etcd.get(
            f"nodes/agents/{agent_id}/watcher_port",
        )
        watcher_port = 6099 if raw_watcher_port is None else int(raw_watcher_port)
        # TODO: watcher scheme is assumed to be http
        addr = yarl.URL(f"http://{agent_ip}:{watcher_port}")
        return {
            "addr": addr,
            "token": token,
        }

    async def sync_agent_registry(
        self, action: SyncAgentRegistryAction
    ) -> SyncAgentRegistryActionResult:
        agent_id = action.agent_id
        await self._agent_registry.sync_agent_kernel_registry(agent_id)
        async with self._db.begin_readonly_session() as db_session:
            agent_row = db_session.scalar(sa.select(AgentRow).where(AgentRow.id == agent_id))

        return SyncAgentRegistryActionResult(result=None, agent_row=agent_row)

    async def get_watcher_status(
        self, action: GetWatcherStatusAction
    ) -> GetWatcherStatusActionResult:
        watcher_info = await self._get_watcher_info(action.agent_id)
        connector = aiohttp.TCPConnector()
        async with aiohttp.ClientSession(connector=connector) as sess:
            # TODO: Ugly naming?
            with _timeout(5.0):
                headers = {"X-BackendAI-Watcher-Token": watcher_info["token"]}
                async with sess.get(watcher_info["addr"], headers=headers) as resp:
                    return GetWatcherStatusActionResult(resp, agent_id=action.agent_id)

    async def watcher_agent_start(
        self, action: WatcherAgentStartAction
    ) -> WatcherAgentStartActionResult:
        watcher_info = await self._get_watcher_info(action.agent_id)
        connector = aiohttp.TCPConnector()
        async with aiohttp.ClientSession(connector=connector) as sess:
            with _timeout(20.0):
                watcher_url = watcher_info["addr"] / "agent/start"
                headers = {"X-BackendAI-Watcher-Token": watcher_info["token"]}
                async with sess.post(watcher_url, headers=headers) as resp:
                    return WatcherAgentStartActionResult(resp, agent_id=action.agent_id)

    async def watcher_agent_restart(
        self, action: WatcherAgentRestartAction
    ) -> WatcherAgentRestartActionResult:
        watcher_info = await self._get_watcher_info(action.agent_id)
        connector = aiohttp.TCPConnector()
        async with aiohttp.ClientSession(connector=connector) as sess:
            with _timeout(20.0):
                watcher_url = watcher_info["addr"] / "agent/restart"
                headers = {"X-BackendAI-Watcher-Token": watcher_info["token"]}
                async with sess.post(watcher_url, headers=headers) as resp:
                    return WatcherAgentRestartActionResult(resp, agent_id=action.agent_id)

    async def watcher_agent_stop(
        self, action: WatcherAgentStopAction
    ) -> WatcherAgentStopActionResult:
        watcher_info = await self._get_watcher_info(action.agent_id)
        connector = aiohttp.TCPConnector()
        async with aiohttp.ClientSession(connector=connector) as sess:
            with _timeout(20.0):
                watcher_url = watcher_info["addr"] / "agent/stop"
                headers = {"X-BackendAI-Watcher-Token": watcher_info["token"]}
                async with sess.post(watcher_url, headers=headers) as resp:
                    return WatcherAgentStopActionResult(resp, agent_id=action.agent_id)

    async def recalculate_usage(
        self, action: RecalculateUsageAction
    ) -> RecalculateUsageActionResult:
        await self._agent_registry.recalc_resource_usage()
        return RecalculateUsageActionResult()
