import logging
from datetime import datetime
from typing import Literal

import aiohttp
import yarl
from async_timeout import timeout as _timeout
from dateutil.tz import tzutc

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.agent.anycast import AgentStartedEvent
from ai.backend.common.exception import (
    AgentWatcherResponseError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.common.types import (
    AgentId,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.agent_cache import AgentRPCCache
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.agent.types import (
    AgentHeartbeatUpsert,
    UpsertResult,
)
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.agent.repository import AgentRepository
from ai.backend.manager.repositories.agent.updaters import AgentStatusUpdaterSpec
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
from ai.backend.manager.services.agent.actions.mark_agent_exit import (
    MarkAgentExitAction,
    MarkAgentExitActionResult,
)
from ai.backend.manager.services.agent.actions.mark_agent_running import (
    MarkAgentRunningAction,
    MarkAgentRunningActionResult,
)
from ai.backend.manager.services.agent.actions.recalculate_usage import (
    RecalculateUsageAction,
    RecalculateUsageActionResult,
)
from ai.backend.manager.services.agent.actions.remove_agent_from_images import (
    RemoveAgentFromImagesAction,
    RemoveAgentFromImagesActionResult,
)
from ai.backend.manager.services.agent.actions.remove_agent_from_images_by_canonicals import (
    RemoveAgentFromImagesByCanonicalsAction,
    RemoveAgentFromImagesByCanonicalsActionResult,
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
from ai.backend.manager.types import OptionalState

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AgentService:
    _etcd: AsyncEtcd
    _config_provider: ManagerConfigProvider
    _agent_registry: AgentRegistry
    _agent_repository: AgentRepository
    _scheduler_repository: SchedulerRepository
    _hook_plugin_ctx: HookPluginContext
    _event_producer: EventProducer
    _agent_cache: AgentRPCCache

    def __init__(
        self,
        etcd: AsyncEtcd,
        agent_registry: AgentRegistry,
        config_provider: ManagerConfigProvider,
        agent_repository: AgentRepository,
        scheduler_repository: SchedulerRepository,
        hook_plugin_ctx: HookPluginContext,
        event_producer: EventProducer,
        agent_cache: AgentRPCCache,
    ) -> None:
        self._etcd = etcd
        self._agent_registry = agent_registry
        self._config_provider = config_provider
        self._agent_repository = agent_repository
        self._scheduler_repository = scheduler_repository
        self._hook_plugin_ctx = hook_plugin_ctx
        self._event_producer = event_producer
        self._agent_cache = agent_cache

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

    async def _request_watcher(
        self,
        agent_id: AgentId,
        method: Literal["GET", "POST"],
        endpoint: str,
    ) -> dict:
        watcher_info = await self._get_watcher_info(agent_id)
        connector = aiohttp.TCPConnector()

        async with aiohttp.ClientSession(connector=connector) as sess:
            with _timeout(5.0):
                watcher_url = watcher_info["addr"] / endpoint
                headers = {"X-BackendAI-Watcher-Token": watcher_info["token"]}

                async with sess.request(method, watcher_url, headers=headers) as resp:
                    if resp.status // 100 == 2:
                        return await resp.json()

                    error_msg = await resp.text()
                    raise AgentWatcherResponseError(
                        status_code=resp.status,
                        error_code=ErrorCode(
                            domain=ErrorDomain.AGENT,
                            operation=ErrorOperation.READ
                            if method == "GET"
                            else ErrorOperation.EXECUTE,
                            error_detail=ErrorDetail.UNAVAILABLE,
                        ),
                        error_message=f"Agent watcher error: {error_msg}",
                    )

    async def get_watcher_status(
        self, action: GetWatcherStatusAction
    ) -> GetWatcherStatusActionResult:
        res = await self._request_watcher(agent_id=action.agent_id, method="GET", endpoint="")
        return GetWatcherStatusActionResult(
            data=res,
            agent_id=action.agent_id,
        )

    async def watcher_agent_start(
        self, action: WatcherAgentStartAction
    ) -> WatcherAgentStartActionResult:
        data = await self._request_watcher(
            agent_id=action.agent_id, method="POST", endpoint="agent/start"
        )
        return WatcherAgentStartActionResult(
            data=data,
            agent_id=action.agent_id,
        )

    async def watcher_agent_restart(
        self, action: WatcherAgentRestartAction
    ) -> WatcherAgentRestartActionResult:
        data = await self._request_watcher(
            agent_id=action.agent_id, method="POST", endpoint="agent/restart"
        )
        return WatcherAgentRestartActionResult(
            data=data,
            agent_id=action.agent_id,
        )

    async def watcher_agent_stop(
        self, action: WatcherAgentStopAction
    ) -> WatcherAgentStopActionResult:
        data = await self._request_watcher(
            agent_id=action.agent_id, method="POST", endpoint="agent/stop"
        )
        return WatcherAgentStopActionResult(
            data=data,
            agent_id=action.agent_id,
        )

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
        reported_agent_info = action.agent_info

        upsert_data = AgentHeartbeatUpsert.from_agent_info(
            agent_id=action.agent_id,
            agent_info=action.agent_info,
            heartbeat_received=datetime.now(tzutc()),
        )
        result: UpsertResult = await self._agent_repository.sync_agent_heartbeat(
            action.agent_id,
            upsert_data,
        )
        self._agent_cache.update(
            action.agent_id,
            reported_agent_info.addr,
            reported_agent_info.public_key,
        )
        if result.was_revived:
            await self._event_producer.anycast_event(
                AgentStartedEvent("revived"), source_override=action.agent_id
            )
        await self._agent_repository.sync_installed_images(agent_id=action.agent_id)

        await self._hook_plugin_ctx.notify(
            "POST_AGENT_HEARTBEAT",
            (
                action.agent_id,
                reported_agent_info.scaling_group,
                reported_agent_info.available_resource_slots,
            ),
        )
        return HandleHeartbeatActionResult(agent_id=action.agent_id)

    async def mark_agent_exit(self, action: MarkAgentExitAction) -> MarkAgentExitActionResult:
        now = datetime.now(tzutc())
        await self._agent_repository.cleanup_agent_on_exit(
            agent_id=action.agent_id,
            spec=AgentStatusUpdaterSpec(
                status=action.agent_status, status_changed=now, lost_at=OptionalState.update(now)
            ),
        )
        self._agent_cache.discard(action.agent_id)
        return MarkAgentExitActionResult(agent_id=action.agent_id)

    async def mark_agent_running(
        self, action: MarkAgentRunningAction
    ) -> MarkAgentRunningActionResult:
        now = datetime.now(tzutc())
        await self._agent_repository.update_agent_status(
            agent_id=action.agent_id,
            spec=AgentStatusUpdaterSpec(
                status=action.agent_status,
                status_changed=now,
            ),
        )
        return MarkAgentRunningActionResult(agent_id=action.agent_id)

    async def remove_agent_from_images(
        self, action: RemoveAgentFromImagesAction
    ) -> RemoveAgentFromImagesActionResult:
        await self._agent_repository.remove_agent_from_images(
            action.agent_id, action.scanned_images
        )

        return RemoveAgentFromImagesActionResult(agent_id=action.agent_id)

    # For compatibility with redis key made with image canonical strings
    # Use remove_agent_from_images instead of this if possible
    async def remove_agent_from_images_by_canonicals(
        self, action: RemoveAgentFromImagesByCanonicalsAction
    ) -> RemoveAgentFromImagesByCanonicalsActionResult:
        await self._agent_repository.remove_agent_from_images_by_canonicals(
            action.agent_id, action.image_canonicals
        )

        return RemoveAgentFromImagesByCanonicalsActionResult(agent_id=action.agent_id)
