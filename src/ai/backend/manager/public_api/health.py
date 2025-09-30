from __future__ import annotations

import asyncio
import logging
import textwrap
from typing import TYPE_CHECKING, cast

import aiohttp_cors
import attrs
from aiohttp import web

from ai.backend.common.types import PromMetric, PromMetricGroup, PromMetricPrimitive
from ai.backend.logging import BraceStyleAdapter

from .. import __version__
from ..dto.response import HealthResponse
from ..models.health import (
    SQLAlchemyConnectionInfo,
    get_manager_db_cxn_status,
    report_manager_status,
)
from .types import CORSOptions

if TYPE_CHECKING:
    from ..api.context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


async def report_status_bgtask(root_ctx: RootContext) -> None:
    interval = cast(float, root_ctx.config_provider.config.manager.status_update_interval)
    try:
        while True:
            await asyncio.sleep(interval)
            try:
                await report_manager_status(root_ctx)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log.exception(f"Failed to report manager health status (e:{str(e)})")
    except asyncio.CancelledError:
        pass


class SQLAlchemyConnectionMetric(PromMetric):
    def __init__(self, node_id: str, pid: int, val: int) -> None:
        self.mgr_id = f"{node_id}:{pid}"
        self.val = val

    def metric_value_string(self, metric_name: str, primitive: PromMetricPrimitive) -> str:
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

    def metric_value_string(self, metric_name: str, primitive: PromMetricPrimitive) -> str:
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


async def hello(request: web.Request) -> web.Response:
    """Simple health check endpoint"""
    request["do_not_print_access_log"] = True

    response = HealthResponse(
        status="healthy",
        version=__version__,
        component="manager",
    )
    return web.json_response(response.model_dump())


async def get_manager_status_for_prom(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    status = await get_manager_db_cxn_status(root_ctx)

    total_cxn_metrics = []
    open_cxn_metrics = []
    closed_cxn_metrics = []
    redis_cxn_metrics = []
    for stat in status:
        sqlalchemy_info = cast(SQLAlchemyConnectionInfo, stat.sqlalchemy_info)

        total_cxn_metrics.append(
            SQLAlchemyConnectionMetric(stat.node_id, stat.pid, sqlalchemy_info.total_cxn)
        )
        open_cxn_metrics.append(
            SQLAlchemyConnectionMetric(stat.node_id, stat.pid, sqlalchemy_info.num_checkedout_cxn)
        )
        closed_cxn_metrics.append(
            SQLAlchemyConnectionMetric(stat.node_id, stat.pid, sqlalchemy_info.num_checkedin_cxn)
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

    result = "\n".join(metric_string)
    return web.Response(text=textwrap.dedent(result))


@attrs.define(slots=True, auto_attribs=True, init=False)
class PrivateContext:
    db_status_report_task: asyncio.Task


async def init(app: web.Application) -> None:
    root_ctx: RootContext = app["_root.context"]
    app_ctx: PrivateContext = app["health.context"]
    app_ctx.db_status_report_task = asyncio.create_task(report_status_bgtask(root_ctx))


async def shutdown(app: web.Application) -> None:
    app_ctx: PrivateContext = app["health.context"]
    if app_ctx.db_status_report_task is not None:
        app_ctx.db_status_report_task.cancel()
        await asyncio.sleep(0)
        if not app_ctx.db_status_report_task.done():
            await app_ctx.db_status_report_task


def create_app(default_cors_options: CORSOptions):
    app = web.Application()
    app["health.context"] = PrivateContext()
    app["prefix"] = "health"
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)

    # Basic health check endpoint
    root_resource = cors.add(app.router.add_resource(r""))
    cors.add(root_resource.add_route("GET", hello))

    prom_resource = cors.add(app.router.add_resource("/prom"))
    cors.add(prom_resource.add_route("GET", get_manager_status_for_prom))

    return app, []
