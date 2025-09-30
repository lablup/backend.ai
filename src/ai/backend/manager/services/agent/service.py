import asyncio
import logging
from datetime import datetime
from decimal import Decimal

import aiohttp
import yarl
from async_timeout import timeout as _timeout
from dateutil.tz import tzutc

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.agent.anycast import AgentStartedEvent
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.common.types import (
    AgentId,
    ResourceSlot,
    SlotName,
    SlotTypes,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.agent.types import (
    AgentHeartbeatUpsert,
    AgentStateSyncData,
    UpsertResult,
)
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.agent.repository import AgentRepository
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.services.agent.actions.get_total_resources import (
    GetTotalResourcesAction,
    GetTotalResourcesActionResult,
)
from ai.backend.manager.services.agent.actions.get_watcher_status import (
    GetWatcherStatusAction,
    GetWatcherStatusActionResult,
)
from ai.backend.manager.services.agent.actions.handle_heartbeat import (
    HandleHeartbeatAction,
    HandleHeartbeatActionResult,
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
    _etcd: AsyncEtcd
    _config_provider: ManagerConfigProvider
    _agent_registry: AgentRegistry
    _agent_repository: AgentRepository
    _scheduler_repository: SchedulerRepository
    _hook_plugin_ctx: HookPluginContext
    _event_producer: EventProducer
    _heartbeat_lock: asyncio.Lock

    def __init__(
        self,
        etcd: AsyncEtcd,
        agent_registry: AgentRegistry,
        config_provider: ManagerConfigProvider,
        agent_repository: AgentRepository,
        scheduler_repository: SchedulerRepository,
        hook_plugin_ctx: HookPluginContext,
        event_producer: EventProducer,
    ) -> None:
        self._etcd = etcd
        self._agent_registry = agent_registry
        self._config_provider = config_provider
        self._agent_repository = agent_repository
        self._scheduler_repository = scheduler_repository
        self._hook_plugin_ctx = hook_plugin_ctx
        self._event_producer = event_producer
        self._heartbeat_lock = asyncio.Lock()

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
        agent_data = await self._agent_repository.get_by_id(agent_id)

        return SyncAgentRegistryActionResult(result=None, agent_data=agent_data)

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

    async def get_total_resources(
        self, action: GetTotalResourcesAction
    ) -> GetTotalResourcesActionResult:
        total_resources = await self._scheduler_repository.get_total_resource_slots()
        return GetTotalResourcesActionResult(total_resources=total_resources)

    async def handle_heartbeat(self, action: HandleHeartbeatAction) -> HandleHeartbeatActionResult:
        now = datetime.now(tzutc())
        reported_agent_info = action.agent_info
        reported_agent_available_slots = ResourceSlot({
            SlotName(k): Decimal(v[1]) for k, v in reported_agent_info["resource_slots"].items()
        })
        reported_agent_sgroup = reported_agent_info.get("scaling_group", "default")

        reported_agent_state_sync_data = AgentStateSyncData(
            now=now,
            slot_key_and_units={
                SlotName(k): SlotTypes(v[0])
                for k, v in reported_agent_info["resource_slots"].items()
            },
            current_addr=reported_agent_info["addr"],
            public_key=reported_agent_info["public_key"],
        )

        async with self._heartbeat_lock:
            upsert_data = AgentHeartbeatUpsert.from_agent_info(
                agent_id=action.agent_id,
                agent_info=action.agent_info,
                heartbeat_received=now,
            )
            result: UpsertResult = await self._agent_repository.sync_agent_heartbeat(
                action.agent_id,
                upsert_data,
                reported_agent_state_sync_data,
            )
            if result.was_revived:
                await self._event_producer.anycast_event(
                    AgentStartedEvent("revived"), source_override=action.agent_id
                )
            self._agent_repository.add_agent_to_images(
                agent_id=action.agent_id, images=action.agent_info["images"]
            )

        await self._hook_plugin_ctx.notify(
            "POST_AGENT_HEARTBEAT",
            (action.agent_id, reported_agent_sgroup, reported_agent_available_slots),
        )
        return HandleHeartbeatActionResult(agent_id=action.agent_id)
