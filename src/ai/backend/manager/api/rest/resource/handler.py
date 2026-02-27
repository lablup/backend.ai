"""Resource handler class using constructor dependency injection.

All handlers use the new ApiHandler pattern: typed parameters
(``BodyParam``, ``QueryParam``, ``UserContext``, ``RequestCtx``) are
automatically extracted by ``_wrap_api_handler`` and responses are
returned as ``web.StreamResponse`` objects.
"""

from __future__ import annotations

import logging
import uuid
from http import HTTPStatus
from typing import Any, Final

from aiohttp import web
from pydantic import AliasChoices, Field, field_validator

from ai.backend.common.api_handlers import BaseRequestModel, BodyParam, QueryParam
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
from ai.backend.manager.services.processors import Processors
from ai.backend.manager.services.resource_preset.actions.check_presets import (
    CheckResourcePresetsAction,
)
from ai.backend.manager.services.resource_preset.actions.list_presets import (
    ListResourcePresetsAction,
)
from ai.backend.manager.services.user.actions.admin_month_stats import AdminMonthStatsAction
from ai.backend.manager.services.user.actions.user_month_stats import UserMonthStatsAction

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class ListPresetsRequest(BaseRequestModel):
    scaling_group: str | None = None


class CheckPresetsRequest(BaseRequestModel):
    scaling_group: str | None = None
    group: str


class UsagePerMonthRequest(BaseRequestModel):
    group_ids: list[uuid.UUID] | None = None
    month: str

    @field_validator("group_ids", mode="before")
    @classmethod
    def parse_group_ids(cls, v: Any) -> Any:
        if v is None:
            return None
        if isinstance(v, str):
            parts = [x.strip() for x in v.split(",") if x.strip()]
            return parts or None
        return v


class UsagePerPeriodRequest(BaseRequestModel):
    project_id: uuid.UUID | None = Field(
        default=None,
        validation_alias=AliasChoices("project_id", "group_id"),
    )
    start_date: str
    end_date: str


class WatcherRequest(BaseRequestModel):
    agent_id: str = Field(validation_alias=AliasChoices("agent_id", "agent"))


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------


class ResourceHandler:
    """Resource API handler with constructor-injected dependencies."""

    def __init__(self, *, processors: Processors) -> None:
        self._processors = processors

    # ------------------------------------------------------------------
    # list_presets (GET /resource/presets)
    # ------------------------------------------------------------------

    async def list_presets(
        self, query: QueryParam[ListPresetsRequest], ctx: UserContext
    ) -> web.StreamResponse:
        log.info("LIST_PRESETS (ak:{})", ctx.access_key)
        params = query.parsed
        result = await self._processors.resource_preset.list_presets.wait_for_complete(
            ListResourcePresetsAction(
                access_key=AccessKey(ctx.access_key),
                scaling_group=params.scaling_group,
            )
        )
        return web.json_response({"presets": result.presets}, status=HTTPStatus.OK)

    # ------------------------------------------------------------------
    # check_presets (POST /resource/check-presets)
    # ------------------------------------------------------------------

    async def check_presets(
        self,
        body: BodyParam[CheckPresetsRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> web.StreamResponse:
        params = body.parsed
        access_key = ctx.access_key
        resource_policy = req.request["keypair"]["resource_policy"]
        domain_name = ctx.user_domain

        log.info(
            "CHECK_PRESETS (ak:{}, g:{}, sg:{})",
            access_key,
            params.group,
            params.scaling_group,
        )

        result = await self._processors.resource_preset.check_presets.wait_for_complete(
            CheckResourcePresetsAction(
                access_key=AccessKey(access_key),
                resource_policy=resource_policy,
                domain_name=domain_name,
                user_id=ctx.user_uuid,
                group=params.group,
                scaling_group=params.scaling_group,
            )
        )

        scaling_groups_json = {}
        for sgname, sg_data in result.scaling_groups.items():
            scaling_groups_json[sgname] = {
                ResourceSlotState.OCCUPIED: quantities_to_json(sg_data[ResourceSlotState.OCCUPIED]),
                ResourceSlotState.AVAILABLE: quantities_to_json(
                    sg_data[ResourceSlotState.AVAILABLE]
                ),
            }

        resp = {
            "presets": result.presets,
            "keypair_limits": quantities_to_json(result.keypair_limits),
            "keypair_using": quantities_to_json(result.keypair_using),
            "keypair_remaining": quantities_to_json(result.keypair_remaining),
            "group_limits": quantities_to_json(result.group_limits),
            "group_using": quantities_to_json(result.group_using),
            "group_remaining": quantities_to_json(result.group_remaining),
            "scaling_group_remaining": quantities_to_json(result.scaling_group_remaining),
            "scaling_groups": scaling_groups_json,
        }

        return web.json_response(resp, status=HTTPStatus.OK)

    # ------------------------------------------------------------------
    # recalculate_usage (POST /resource/recalculate-usage)
    # ------------------------------------------------------------------

    async def recalculate_usage(self) -> web.StreamResponse:
        log.info("RECALCULATE_USAGE ()")
        await self._processors.agent.recalculate_usage.wait_for_complete(RecalculateUsageAction())
        return web.json_response({}, status=HTTPStatus.OK)

    # ------------------------------------------------------------------
    # usage_per_month (GET /resource/usage/month)
    # ------------------------------------------------------------------

    async def usage_per_month(self, query: QueryParam[UsagePerMonthRequest]) -> web.StreamResponse:
        params = query.parsed
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
        return web.json_response(result.result, status=HTTPStatus.OK)

    # ------------------------------------------------------------------
    # usage_per_period (GET /resource/usage/period)
    # ------------------------------------------------------------------

    async def usage_per_period(
        self, query: QueryParam[UsagePerPeriodRequest]
    ) -> web.StreamResponse:
        params = query.parsed
        result = await self._processors.group.usage_per_period.wait_for_complete(
            UsagePerPeriodAction(
                project_id=params.project_id,
                start_date=params.start_date,
                end_date=params.end_date,
            )
        )
        return web.json_response(result.result, status=HTTPStatus.OK)

    # ------------------------------------------------------------------
    # user_month_stats (GET /resource/stats/user/month)
    # ------------------------------------------------------------------

    async def user_month_stats(self, ctx: UserContext) -> web.StreamResponse:
        log.info("USER_LAST_MONTH_STATS (ak:{}, u:{})", ctx.access_key, ctx.user_uuid)
        result = await self._processors.user.user_month_stats.wait_for_complete(
            UserMonthStatsAction(user_id=ctx.user_uuid)
        )
        return web.json_response(result.stats, status=HTTPStatus.OK)

    # ------------------------------------------------------------------
    # admin_month_stats (GET /resource/stats/admin/month)
    # ------------------------------------------------------------------

    async def admin_month_stats(self) -> web.StreamResponse:
        log.info("ADMIN_LAST_MONTH_STATS ()")
        result = await self._processors.user.admin_month_stats.wait_for_complete(
            AdminMonthStatsAction()
        )
        return web.json_response(result.stats, status=HTTPStatus.OK)

    # ------------------------------------------------------------------
    # get_watcher_status (GET /resource/watcher)
    # ------------------------------------------------------------------

    async def get_watcher_status(self, query: QueryParam[WatcherRequest]) -> web.StreamResponse:
        params = query.parsed
        log.info("GET_WATCHER_STATUS (ag:{})", params.agent_id)
        result = await self._processors.agent.get_watcher_status.wait_for_complete(
            GetWatcherStatusAction(agent_id=AgentId(params.agent_id))
        )
        return web.json_response(result.data, status=HTTPStatus.OK)

    # ------------------------------------------------------------------
    # watcher_agent_start (POST /resource/watcher/agent/start)
    # ------------------------------------------------------------------

    async def watcher_agent_start(self, body: BodyParam[WatcherRequest]) -> web.StreamResponse:
        params = body.parsed
        log.info("WATCHER_AGENT_START (ag:{})", params.agent_id)
        result = await self._processors.agent.watcher_agent_start.wait_for_complete(
            WatcherAgentStartAction(agent_id=AgentId(params.agent_id))
        )
        return web.json_response(result.data, status=HTTPStatus.OK)

    # ------------------------------------------------------------------
    # watcher_agent_stop (POST /resource/watcher/agent/stop)
    # ------------------------------------------------------------------

    async def watcher_agent_stop(self, body: BodyParam[WatcherRequest]) -> web.StreamResponse:
        params = body.parsed
        log.info("WATCHER_AGENT_STOP (ag:{})", params.agent_id)
        result = await self._processors.agent.watcher_agent_stop.wait_for_complete(
            WatcherAgentStopAction(agent_id=AgentId(params.agent_id))
        )
        return web.json_response(result.data, status=HTTPStatus.OK)

    # ------------------------------------------------------------------
    # watcher_agent_restart (POST /resource/watcher/agent/restart)
    # ------------------------------------------------------------------

    async def watcher_agent_restart(self, body: BodyParam[WatcherRequest]) -> web.StreamResponse:
        params = body.parsed
        log.info("WATCHER_AGENT_RESTART (ag:{})", params.agent_id)
        result = await self._processors.agent.watcher_agent_restart.wait_for_complete(
            WatcherAgentRestartAction(
                agent_id=AgentId(params.agent_id),
            )
        )
        return web.json_response(result.data, status=HTTPStatus.OK)

    # ------------------------------------------------------------------
    # get_container_registries (GET /resource/container-registries)
    # ------------------------------------------------------------------

    async def get_container_registries(self) -> web.StreamResponse:
        result = (
            await self._processors.container_registry.get_container_registries.wait_for_complete(
                GetContainerRegistriesAction()
            )
        )
        return web.json_response(result.registries, status=HTTPStatus.OK)
