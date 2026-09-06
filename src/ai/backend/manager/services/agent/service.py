import logging
from typing import Any, Literal, cast
from uuid import UUID

import aiohttp
import yarl
from async_timeout import timeout as _timeout

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.exception import (
    AgentWatcherResponseError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.common.types import (
    AgentId,
    SessionId,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.errors.agent import ConflictingSessionRescheduleNotSupported
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
from ai.backend.manager.services.agent.actions.load_container_counts import (
    LoadContainerCountsAction,
    LoadContainerCountsActionResult,
)
from ai.backend.manager.services.agent.actions.recalculate_usage import (
    RecalculateUsageAction,
    RecalculateUsageActionResult,
)
from ai.backend.manager.services.agent.actions.search_agents import (
    SearchAgentsAction,
    SearchAgentsActionResult,
)
from ai.backend.manager.services.agent.actions.sync_agent_registry import (
    SyncAgentRegistryAction,
    SyncAgentRegistryActionResult,
)
from ai.backend.manager.services.agent.actions.update_resource_group import (
    UpdateAgentResourceGroupAction,
    UpdateAgentResourceGroupActionResult,
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
from ai.backend.manager.services.agent.types import ConflictingSessionCleanupPolicy
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_RESOURCE_GROUP_CHANGED_REASON = "AGENT_RESOURCE_GROUP_CHANGED"


class AgentService:
    _etcd: AsyncEtcd
    _config_provider: ManagerConfigProvider
    _agent_registry: AgentRegistry
    _agent_repository: AgentRepository
    _scheduler_repository: SchedulerRepository
    _scheduling_controller: SchedulingController

    def __init__(
        self,
        etcd: AsyncEtcd,
        agent_registry: AgentRegistry,
        config_provider: ManagerConfigProvider,
        agent_repository: AgentRepository,
        scheduler_repository: SchedulerRepository,
        scheduling_controller: SchedulingController,
    ) -> None:
        self._etcd = etcd
        self._agent_registry = agent_registry
        self._config_provider = config_provider
        self._agent_repository = agent_repository
        self._scheduler_repository = scheduler_repository
        self._scheduling_controller = scheduling_controller

    async def _get_watcher_info(self, agent_id: AgentId) -> dict[str, Any]:
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

    async def update_resource_group(
        self, action: UpdateAgentResourceGroupAction
    ) -> UpdateAgentResourceGroupActionResult:
        """
        Change an agent's resource group, handling the sessions running on it.

        The repository atomically gates on the agent's active sessions (raising
        AgentHasConflictingSessions when they exist and ``force`` is unset),
        commits the group change, and returns those sessions. The returned
        sessions are then transitioned per ``policy``; their cleanup proceeds
        asynchronously. ``RESCHEDULE`` is not implemented yet.
        """
        agent_id = action.agent_id
        if action.policy is ConflictingSessionCleanupPolicy.RESCHEDULE:
            # Rejected up front so no group change or termination happens.
            raise ConflictingSessionRescheduleNotSupported()

        kernels = await self._agent_repository.update_resource_group(
            agent_id, action.resource_group_id, force=action.force
        )
        conflicting_session_ids = list({
            SessionId(UUID(kernel.session.session_id)) for kernel in kernels
        })

        terminating_session_ids: list[SessionId] = []
        if conflicting_session_ids:
            # Graceful termination: sessions transition to TERMINATING and the
            # container cleanup proceeds asynchronously in the next schedule cycle.
            mark_result = await self._scheduling_controller.mark_sessions_for_termination(
                conflicting_session_ids,
                reason=_RESOURCE_GROUP_CHANGED_REASON,
                forced=False,
            )
            terminating_session_ids = mark_result.terminating_sessions

        return UpdateAgentResourceGroupActionResult(
            agent_id=agent_id,
            resource_group_id=action.resource_group_id,
            conflicting_session_ids=conflicting_session_ids,
            terminating_session_ids=terminating_session_ids,
        )

    async def _request_watcher(
        self,
        agent_id: AgentId,
        method: Literal["GET", "POST"],
        endpoint: str,
    ) -> dict[str, Any]:
        watcher_info = await self._get_watcher_info(agent_id)
        connector = aiohttp.TCPConnector()

        async with aiohttp.ClientSession(connector=connector) as sess:
            with _timeout(5.0):
                watcher_url = watcher_info["addr"] / endpoint
                headers = {"X-BackendAI-Watcher-Token": watcher_info["token"]}

                async with sess.request(method, watcher_url, headers=headers) as resp:
                    if resp.status // 100 == 2:
                        return cast(dict[str, Any], await resp.json())

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
        self, _action: RecalculateUsageAction
    ) -> RecalculateUsageActionResult:
        await self._agent_registry.recalc_resource_usage()
        return RecalculateUsageActionResult()

    async def get_total_resources(
        self, _action: GetTotalResourcesAction
    ) -> GetTotalResourcesActionResult:
        total_resources = await self._scheduler_repository.get_total_resource_slots()
        return GetTotalResourcesActionResult(total_resources=total_resources)

    async def search_agents(self, action: SearchAgentsAction) -> SearchAgentsActionResult:
        """Searches agents. It is used by superadmin only."""
        result = await self._agent_repository.search_agents(
            querier=action.querier,
        )

        return SearchAgentsActionResult(
            agents=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def load_container_counts(
        self, action: LoadContainerCountsAction
    ) -> LoadContainerCountsActionResult:
        container_counts = await self._agent_repository.load_agent_container_counts(
            agent_ids=action.agent_ids
        )
        return LoadContainerCountsActionResult(container_counts=container_counts)
