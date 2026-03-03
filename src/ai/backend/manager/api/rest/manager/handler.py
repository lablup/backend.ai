"""Manager API handler using constructor dependency injection.

All handlers use the new ApiHandler pattern: typed parameters
(``BodyParam``, ``QueryParam``, ``UserContext``, ``RequestCtx``) are
automatically extracted by ``_wrap_api_handler`` and responses are
returned as ``APIResponse`` objects.

Note: ``get_manager_status_for_prom`` returns ``web.Response`` (plain text)
directly because Prometheus exposition format is not JSON.
"""

from __future__ import annotations

import logging
import textwrap
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, Final

import trafaret as t
from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BodyParam
from ai.backend.common.dto.manager.manager_api.request import (
    SchedulerOps,
    SchedulerOpsRequest,
    UpdateAnnouncementRequest,
    UpdateManagerStatusRequest,
)
from ai.backend.common.dto.manager.manager_api.response import (
    AnnouncementResponse,
    ManagerStatusResponse,
)
from ai.backend.common.types import PromMetric, PromMetricGroup, PromMetricPrimitive
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager import __version__
from ai.backend.manager.dto.context import RequestCtx, UserContext
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.services.manager_admin import (
    FetchManagerStatusAction,
    GetAnnouncementAction,
    GetDbCxnStatusAction,
    PerformSchedulerOpsAction,
    UpdateAnnouncementAction,
    UpdateManagerStatusAction,
)

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Trafaret validators for scheduler ops arguments
_iv_scheduler_ops_args = {
    SchedulerOps.INCLUDE_AGENTS: t.List(t.String),
    SchedulerOps.EXCLUDE_AGENTS: t.List(t.String),
}


# ------------------------------------------------------------------
# Prometheus metric helpers (kept here as they are handler-specific)
# ------------------------------------------------------------------


class SQLAlchemyConnectionMetric(PromMetric):
    def __init__(self, node_id: str, pid: int, val: int) -> None:
        self.mgr_id = f"{node_id}:{pid}"
        self.val = val

    def metric_value_string(self, metric_name: str, _primitive: PromMetricPrimitive) -> str:
        return f"""{metric_name}{{mgr_id="{self.mgr_id}"}} {self.val}"""


class SQLAlchemyTotalConnectionMetricGroup(PromMetricGroup[SQLAlchemyConnectionMetric]):
    @property
    def metric_name(self) -> str:
        return "sqlalchemy_total_connection"

    @property
    def description(self) -> str:
        return "The number of total connections in SQLAlchemy connection pool."

    @property
    def metric_primitive(self) -> PromMetricPrimitive:
        return PromMetricPrimitive.gauge


class SQLAlchemyOpenConnectionMetricGroup(PromMetricGroup[SQLAlchemyConnectionMetric]):
    @property
    def metric_name(self) -> str:
        return "sqlalchemy_open_connection"

    @property
    def description(self) -> str:
        return "The number of open connections in SQLAlchemy connection pool."

    @property
    def metric_primitive(self) -> PromMetricPrimitive:
        return PromMetricPrimitive.gauge


class SQLAlchemyClosedConnectionMetricGroup(PromMetricGroup[SQLAlchemyConnectionMetric]):
    @property
    def metric_name(self) -> str:
        return "sqlalchemy_closed_connection"

    @property
    def description(self) -> str:
        return "The number of closed connections in SQLAlchemy connection pool."

    @property
    def metric_primitive(self) -> PromMetricPrimitive:
        return PromMetricPrimitive.gauge


class RedisConnectionMetric(PromMetric):
    def __init__(self, node_id: str, pid: int, redis_obj_name: str, val: int) -> None:
        self.redis_obj_name = redis_obj_name
        self.mgr_id = f"{node_id}:{pid}"
        self.val = val

    def metric_value_string(self, metric_name: str, _primitive: PromMetricPrimitive) -> str:
        return (
            f"""{metric_name}{{mgr_id="{self.mgr_id}",name="{self.redis_obj_name}"}} {self.val}"""
        )


class RedisConnectionMetricGroup(PromMetricGroup[RedisConnectionMetric]):
    @property
    def metric_name(self) -> str:
        return "redis_connection"

    @property
    def description(self) -> str:
        return "The number of connections in Redis Client's connection pool."

    @property
    def metric_primitive(self) -> PromMetricPrimitive:
        return PromMetricPrimitive.gauge


# ------------------------------------------------------------------
# Handler class
# ------------------------------------------------------------------


class ManagerHandler:
    """Manager API handler with constructor-injected dependencies."""

    def __init__(self, *, processors: Processors) -> None:
        self._processors = processors

    # ------------------------------------------------------------------
    # fetch_manager_status (GET /manager/status)
    # ------------------------------------------------------------------

    async def fetch_manager_status(self, req: RequestCtx) -> APIResponse:
        log.info("MANAGER.FETCH_MANAGER_STATUS ()")
        try:
            action = FetchManagerStatusAction()
            result = await self._processors.manager_admin.fetch_status.wait_for_complete(action)
            nodes = [
                {
                    "id": result.manager_id,
                    "num_proc": result.num_proc,
                    "service_addr": result.service_addr,
                    "heartbeat_timeout": result.heartbeat_timeout,
                    "ssl_enabled": result.ssl_enabled,
                    "active_sessions": result.active_sessions,
                    "status": result.status,
                    "version": __version__,
                    "api_version": req.request["api_version"],
                },
            ]
            resp = ManagerStatusResponse(
                nodes=nodes,
                status=result.status,
                active_sessions=result.active_sessions,
            )
            return APIResponse.build(HTTPStatus.OK, resp)
        except Exception:
            log.exception("GET_MANAGER_STATUS: exception")
            raise

    # ------------------------------------------------------------------
    # update_manager_status (PUT /manager/status)
    # ------------------------------------------------------------------

    async def update_manager_status(
        self,
        body: BodyParam[UpdateManagerStatusRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = body.parsed
        log.info(
            "MANAGER.UPDATE_MANAGER_STATUS (status:{}, force_kill:{})",
            params.status,
            params.force_kill,
        )
        action = UpdateManagerStatusAction(
            status=params.status,
            force_kill=params.force_kill,
        )
        await self._processors.manager_admin.update_status.wait_for_complete(action)
        return APIResponse.no_content(HTTPStatus.NO_CONTENT)

    # ------------------------------------------------------------------
    # get_announcement (GET /manager/announcement)
    # ------------------------------------------------------------------

    async def get_announcement(self) -> APIResponse:
        action = GetAnnouncementAction()
        result = await self._processors.manager_admin.get_announcement.wait_for_complete(action)
        resp = AnnouncementResponse(enabled=result.enabled, message=result.message)
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # update_announcement (POST /manager/announcement)
    # ------------------------------------------------------------------

    async def update_announcement(
        self,
        body: BodyParam[UpdateAnnouncementRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = body.parsed
        action = UpdateAnnouncementAction(
            enabled=params.enabled,
            message=params.message,
        )
        await self._processors.manager_admin.update_announcement.wait_for_complete(action)
        return APIResponse.no_content(HTTPStatus.NO_CONTENT)

    # ------------------------------------------------------------------
    # perform_scheduler_ops (POST /manager/scheduler/operation)
    # ------------------------------------------------------------------

    async def perform_scheduler_ops(
        self,
        body: BodyParam[SchedulerOpsRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = body.parsed
        op = SchedulerOps(params.op)
        try:
            args: Any = _iv_scheduler_ops_args[op].check(params.args)
        except t.DataError as e:
            raise InvalidAPIParameters(
                f"Input validation failed for args with {op}",
                extra_data=e.as_dict(),
            ) from e
        if op in (SchedulerOps.INCLUDE_AGENTS, SchedulerOps.EXCLUDE_AGENTS):
            schedulable = op == SchedulerOps.INCLUDE_AGENTS
            action = PerformSchedulerOpsAction(
                agent_ids=args,
                schedulable=schedulable,
            )
            await self._processors.manager_admin.perform_scheduler_ops.wait_for_complete(action)
        else:
            raise GenericBadRequest("Unknown scheduler operation")
        return APIResponse.no_content(HTTPStatus.NO_CONTENT)

    # ------------------------------------------------------------------
    # scheduler_trigger (POST /manager/scheduler/trigger)
    # ------------------------------------------------------------------

    async def scheduler_trigger(self, ctx: UserContext) -> APIResponse:
        raise InvalidAPIParameters("Legacy scheduler trigger API is no longer supported")

    # ------------------------------------------------------------------
    # scheduler_healthcheck (GET /manager/scheduler/status)
    # ------------------------------------------------------------------

    async def scheduler_healthcheck(self, ctx: UserContext) -> APIResponse:
        raise InvalidAPIParameters("Legacy scheduler healthcheck API is no longer supported")

    # ------------------------------------------------------------------
    # get_manager_status_for_prom (GET /manager/prom)
    # ------------------------------------------------------------------

    async def get_manager_status_for_prom(self) -> web.StreamResponse:
        action = GetDbCxnStatusAction()
        result = await self._processors.manager_admin.get_db_cxn_status.wait_for_complete(action)
        status = result.cxn_infos

        total_cxn_metrics: list[SQLAlchemyConnectionMetric] = []
        open_cxn_metrics: list[SQLAlchemyConnectionMetric] = []
        closed_cxn_metrics: list[SQLAlchemyConnectionMetric] = []
        redis_cxn_metrics: list[RedisConnectionMetric] = []
        for stat in status:
            sqlalchemy_info = stat.sqlalchemy_info

            total_cxn_metrics.append(
                SQLAlchemyConnectionMetric(stat.node_id, stat.pid, sqlalchemy_info.total_cxn)
            )
            open_cxn_metrics.append(
                SQLAlchemyConnectionMetric(
                    stat.node_id, stat.pid, sqlalchemy_info.num_checkedout_cxn
                )
            )
            closed_cxn_metrics.append(
                SQLAlchemyConnectionMetric(
                    stat.node_id, stat.pid, sqlalchemy_info.num_checkedin_cxn
                )
            )

            for redis_info in stat.redis_connection_info:
                if (num_cxn := redis_info.num_connections) is not None:
                    redis_cxn_metrics.append(
                        RedisConnectionMetric(stat.node_id, stat.pid, redis_info.name, num_cxn)
                    )

        metric_string = (
            SQLAlchemyTotalConnectionMetricGroup(total_cxn_metrics).metric_string(),
            SQLAlchemyOpenConnectionMetricGroup(open_cxn_metrics).metric_string(),
            SQLAlchemyClosedConnectionMetricGroup(closed_cxn_metrics).metric_string(),
            RedisConnectionMetricGroup(redis_cxn_metrics).metric_string(),
        )

        prom_output = "\n".join(metric_string)
        return web.Response(text=textwrap.dedent(prom_output))
