"""Error log module registrar.

Lifecycle management (GlobalTimer for log cleanup, event dispatcher
integration) is handled directly here instead of the legacy
``api.logs`` shim.
"""

from __future__ import annotations

import datetime as dt
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final

import attrs
import sqlalchemy as sa
from aiohttp import web
from dateutil.relativedelta import relativedelta

from ai.backend.common import validators as tx
from ai.backend.common.distributed import GlobalTimer
from ai.backend.common.events.dispatcher import EventHandler
from ai.backend.common.events.event_types.log.anycast import DoLogCleanupEvent
from ai.backend.common.types import AgentId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.server_status import READ_ALLOWED, server_status_required
from ai.backend.manager.defs import LockID
from ai.backend.manager.models.error_logs import error_logs

if TYPE_CHECKING:
    from ai.backend.manager.api.context import RootContext
    from ai.backend.manager.api.rest.types import ModuleDeps

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


async def _log_cleanup_task(app: web.Application, _src: AgentId, _event: DoLogCleanupEvent) -> None:
    root_ctx: RootContext = app["_root.context"]
    raw_lifetime = await root_ctx.etcd.get("config/logs/error/retention")
    if raw_lifetime is None:
        raw_lifetime = "90d"
    lifetime: dt.timedelta | relativedelta
    try:
        lifetime = tx.TimeDuration().check(raw_lifetime)
    except ValueError:
        lifetime = dt.timedelta(days=90)
        log.warning(
            "Failed to parse the error log retention period ({}) read from etcd; "
            "falling back to 90 days",
            raw_lifetime,
        )
    boundary = datetime.now(UTC) - lifetime
    async with root_ctx.db.begin() as conn:
        query = sa.delete(error_logs).where(error_logs.c.created_at < boundary)
        result = await conn.execute(query)
        if result.rowcount > 0:
            log.info("Cleaned up {} log(s) filed before {}", result.rowcount, boundary)


@attrs.define(slots=True, auto_attribs=True, init=False)
class _LogsContext:
    log_cleanup_timer: GlobalTimer
    log_cleanup_timer_evh: EventHandler[web.Application, DoLogCleanupEvent]


async def _logs_startup(app: web.Application) -> None:
    root_ctx: RootContext = app["_root.context"]
    ctx: _LogsContext = app["logs.context"]
    ctx.log_cleanup_timer_evh = root_ctx.event_dispatcher.consume(
        DoLogCleanupEvent,
        app,
        _log_cleanup_task,
    )
    ctx.log_cleanup_timer = GlobalTimer(
        root_ctx.distributed_lock_factory(LockID.LOCKID_LOG_CLEANUP_TIMER, 20.0),
        root_ctx.event_producer,
        lambda: DoLogCleanupEvent(),
        20.0,
        initial_delay=17.0,
        task_name="log_cleanup_task",
    )
    await ctx.log_cleanup_timer.join()


async def _logs_shutdown(app: web.Application) -> None:
    root_ctx: RootContext = app["_root.context"]
    ctx: _LogsContext = app["logs.context"]
    await ctx.log_cleanup_timer.leave()
    root_ctx.event_dispatcher.unconsume(ctx.log_cleanup_timer_evh)


def register_error_log_routes(deps: ModuleDeps) -> RouteRegistry:
    """Build the error log sub-application."""
    from .handler import ErrorLogHandler

    reg = RouteRegistry.create("logs", deps.cors_options)
    ctx = _LogsContext()
    reg.app["logs.context"] = ctx

    # Wire lifecycle hooks
    reg.app.on_startup.append(_logs_startup)
    reg.app.on_shutdown.append(_logs_shutdown)
    handler = ErrorLogHandler(processors=deps.processors)

    reg.add(
        "POST",
        "/error",
        handler.append,
        middlewares=[server_status_required(READ_ALLOWED, deps.config_provider), auth_required],
    )
    reg.add(
        "GET",
        "/error",
        handler.list_logs,
        middlewares=[auth_required, server_status_required(READ_ALLOWED, deps.config_provider)],
    )
    reg.add(
        "POST",
        "/error/{log_id}/clear",
        handler.mark_cleared,
        middlewares=[auth_required, server_status_required(READ_ALLOWED, deps.config_provider)],
    )
    return reg
