"""Resource preset API handler using constructor dependency injection.

All handlers use the new ApiHandler pattern: typed parameters
(``BodyParam``, ``QueryParam``, ``UserContext``) are automatically
extracted by ``_wrap_api_handler`` and responses are returned as
``APIResponse`` objects.
"""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, QueryParam
from ai.backend.common.dto.manager.resource.request import (
    CheckPresetsRequest,
    ListPresetsQuery,
    UsagePerMonthRequest,
    UsagePerPeriodRequest,
    WatcherAgentRequest,
)
from ai.backend.common.dto.manager.resource.response import (
    CheckPresetsResponse,
    ContainerRegistriesResponse,
    EmptyResponse,
    ListPresetsResponse,
    RawListResponse,
    WatcherDataResponse,
)
from ai.backend.common.types import AccessKey, AgentId
from ai.backend.common.types import LegacyResourceSlotState as ResourceSlotState
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.dto.context import RequestCtx, UserContext
from ai.backend.manager.repositories.resource_slot.types import quantities_to_json
from ai.backend.manager.services.agent.actions.get_watcher_status import GetWatcherStatusAction
from ai.backend.manager.services.agent.actions.recalculate_usage import RecalculateUsageAction
from ai.backend.manager.services.agent.actions.watcher_agent_restart import (
    WatcherAgentRestartAction,
)
from ai.backend.manager.services.agent.actions.watcher_agent_start import WatcherAgentStartAction
from ai.backend.manager.services.agent.actions.watcher_agent_stop import WatcherAgentStopAction
from ai.backend.manager.services.container_registry.actions.get_container_registries import (
    GetContainerRegistriesAction,
)
from ai.backend.manager.services.group.actions.usage_per_month import UsagePerMonthAction
from ai.backend.manager.services.group.actions.usage_per_period import UsagePerPeriodAction
from ai.backend.manager.services.resource_preset.actions.check_presets import (
    CheckResourcePresetsAction,
)
from ai.backend.manager.services.resource_preset.actions.list_presets import (
    ListResourcePresetsAction,
)
from ai.backend.manager.services.user.actions.admin_month_stats import AdminMonthStatsAction
from ai.backend.manager.services.user.actions.user_month_stats import UserMonthStatsAction

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ResourceHandler:
    """Resource preset API handler with constructor-injected dependencies."""

    def __init__(self, *, processors: Processors) -> None:
        self._processors = processors

    # ------------------------------------------------------------------
    # list_presets (GET /resource/presets)
    # ------------------------------------------------------------------

    async def list_presets(
        self,
        query: QueryParam[ListPresetsQuery],
        ctx: UserContext,
    ) -> APIResponse:
        log.info("LIST_PRESETS (ak:{})", ctx.access_key)
        params = query.parsed
        result = await self._processors.resource_preset.list_presets.wait_for_complete(
            ListResourcePresetsAction(
                access_key=ctx.access_key,
                scaling_group=params.scaling_group,
            )
        )
        return APIResponse.build(HTTPStatus.OK, ListPresetsResponse(presets=result.presets))

    # ------------------------------------------------------------------
    # check_presets (POST /resource/check-presets)
    # ------------------------------------------------------------------

    async def check_presets(
        self,
        body: BodyParam[CheckPresetsRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        resource_policy = req.request["keypair"]["resource_policy"]
        log.info(
            "CHECK_PRESETS (ak:{}, g:{}, sg:{})",
            ctx.access_key,
            params.group,
            params.scaling_group,
        )
        result = await self._processors.resource_preset.check_presets.wait_for_complete(
            CheckResourcePresetsAction(
                access_key=AccessKey(ctx.access_key),
                resource_policy=resource_policy,
                domain_name=ctx.user_domain,
                user_id=ctx.user_uuid,
                group=params.group,
                scaling_group=params.scaling_group,
            )
        )
        scaling_groups_json: dict[str, Any] = {}
        for sgname, sg_data in result.scaling_groups.items():
            scaling_groups_json[sgname] = {
                ResourceSlotState.OCCUPIED: quantities_to_json(sg_data[ResourceSlotState.OCCUPIED]),
                ResourceSlotState.AVAILABLE: quantities_to_json(
                    sg_data[ResourceSlotState.AVAILABLE]
                ),
            }
        resp = CheckPresetsResponse(
            presets=result.presets,
            keypair_limits=quantities_to_json(result.keypair_limits),
            keypair_using=quantities_to_json(result.keypair_using),
            keypair_remaining=quantities_to_json(result.keypair_remaining),
            group_limits=quantities_to_json(result.group_limits),
            group_using=quantities_to_json(result.group_using),
            group_remaining=quantities_to_json(result.group_remaining),
            scaling_group_remaining=quantities_to_json(result.scaling_group_remaining),
            scaling_groups=scaling_groups_json,
        )
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # recalculate_usage (POST /resource/recalculate-usage)
    # ------------------------------------------------------------------

    async def recalculate_usage(self, ctx: UserContext) -> APIResponse:
        log.info("RECALCULATE_USAGE ()")
        await self._processors.agent.recalculate_usage.wait_for_complete(RecalculateUsageAction())
        return APIResponse.build(HTTPStatus.OK, EmptyResponse())

    # ------------------------------------------------------------------
    # usage_per_month (GET /resource/usage/month)
    # ------------------------------------------------------------------

    async def usage_per_month(
        self,
        body: BodyParam[UsagePerMonthRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = body.parsed
        log.info(
            "USAGE_PER_MONTH (g:[{}], month:{})",
            ",".join(str(gid) for gid in params.group_ids) if params.group_ids else "",
            params.month,
        )
        result = await self._processors.group.usage_per_month.wait_for_complete(
            UsagePerMonthAction(
                group_ids=params.group_ids,
                month=params.month,
            )
        )
        return APIResponse.build(HTTPStatus.OK, RawListResponse(root=result.result))

    # ------------------------------------------------------------------
    # usage_per_period (GET /resource/usage/period)
    # ------------------------------------------------------------------

    async def usage_per_period(
        self,
        body: BodyParam[UsagePerPeriodRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = body.parsed
        result = await self._processors.group.usage_per_period.wait_for_complete(
            UsagePerPeriodAction(
                project_id=params.project_id,
                start_date=params.start_date,
                end_date=params.end_date,
            )
        )
        return APIResponse.build(HTTPStatus.OK, RawListResponse(root=result.result))

    # ------------------------------------------------------------------
    # user_month_stats (GET /resource/stats/user/month)
    # ------------------------------------------------------------------

    async def user_month_stats(self, ctx: UserContext) -> APIResponse:
        log.info("USER_LAST_MONTH_STATS (ak:{}, u:{})", ctx.access_key, ctx.user_uuid)
        result = await self._processors.user.user_month_stats.wait_for_complete(
            UserMonthStatsAction(user_id=ctx.user_uuid)
        )
        return APIResponse.build(HTTPStatus.OK, RawListResponse(root=result.stats))

    # ------------------------------------------------------------------
    # admin_month_stats (GET /resource/stats/admin/month)
    # ------------------------------------------------------------------

    async def admin_month_stats(self, ctx: UserContext) -> APIResponse:
        log.info("ADMIN_LAST_MONTH_STATS ()")
        result = await self._processors.user.admin_month_stats.wait_for_complete(
            AdminMonthStatsAction()
        )
        return APIResponse.build(HTTPStatus.OK, RawListResponse(root=result.stats))

    # ------------------------------------------------------------------
    # get_watcher_status (GET /resource/watcher)
    # ------------------------------------------------------------------

    async def get_watcher_status(
        self,
        body: BodyParam[WatcherAgentRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = body.parsed
        log.info("GET_WATCHER_STATUS (ag:{})", params.agent_id)
        result = await self._processors.agent.get_watcher_status.wait_for_complete(
            GetWatcherStatusAction(agent_id=AgentId(params.agent_id))
        )
        return APIResponse.build(HTTPStatus.OK, WatcherDataResponse(root=result.data))

    # ------------------------------------------------------------------
    # watcher_agent_start (POST /resource/watcher/agent/start)
    # ------------------------------------------------------------------

    async def watcher_agent_start(
        self,
        body: BodyParam[WatcherAgentRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = body.parsed
        log.info("WATCHER_AGENT_START (ag:{})", params.agent_id)
        result = await self._processors.agent.watcher_agent_start.wait_for_complete(
            WatcherAgentStartAction(agent_id=AgentId(params.agent_id))
        )
        return APIResponse.build(HTTPStatus.OK, WatcherDataResponse(root=result.data))

    # ------------------------------------------------------------------
    # watcher_agent_stop (POST /resource/watcher/agent/stop)
    # ------------------------------------------------------------------

    async def watcher_agent_stop(
        self,
        body: BodyParam[WatcherAgentRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = body.parsed
        log.info("WATCHER_AGENT_STOP (ag:{})", params.agent_id)
        result = await self._processors.agent.watcher_agent_stop.wait_for_complete(
            WatcherAgentStopAction(agent_id=AgentId(params.agent_id))
        )
        return APIResponse.build(HTTPStatus.OK, WatcherDataResponse(root=result.data))

    # ------------------------------------------------------------------
    # watcher_agent_restart (POST /resource/watcher/agent/restart)
    # ------------------------------------------------------------------

    async def watcher_agent_restart(
        self,
        body: BodyParam[WatcherAgentRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = body.parsed
        log.info("WATCHER_AGENT_RESTART (ag:{})", params.agent_id)
        result = await self._processors.agent.watcher_agent_restart.wait_for_complete(
            WatcherAgentRestartAction(agent_id=AgentId(params.agent_id))
        )
        return APIResponse.build(HTTPStatus.OK, WatcherDataResponse(root=result.data))

    # ------------------------------------------------------------------
    # get_container_registries (GET /resource/container-registries)
    # ------------------------------------------------------------------

    async def get_container_registries(self, ctx: UserContext) -> APIResponse:
        result = (
            await self._processors.container_registry.get_container_registries.wait_for_complete(
                GetContainerRegistriesAction()
            )
        )
        return APIResponse.build(HTTPStatus.OK, ContainerRegistriesResponse(root=result.registries))
