"""Backward-compatibility shim for the logs module.

All error log handler logic has been migrated to:

* ``api.rest.error_log`` — ErrorLogHandler + route registration

This module keeps ``create_app()`` with the ``PrivateContext`` and
background timer so that the existing server bootstrap continues to work.
The ``GlobalTimer`` for log cleanup and the event dispatcher integration
remain here until the lifecycle is fully migrated to the new system.
"""

from __future__ import annotations

import datetime as dt
import logging
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import TYPE_CHECKING

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
from ai.backend.manager.defs import LockID
from ai.backend.manager.models.error_logs import error_logs

from .types import CORSOptions, WebMiddleware

if TYPE_CHECKING:
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


async def log_cleanup_task(app: web.Application, _src: AgentId, _event: DoLogCleanupEvent) -> None:
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
class PrivateContext:
    log_cleanup_timer: GlobalTimer
    log_cleanup_timer_evh: EventHandler[web.Application, DoLogCleanupEvent]


async def init(app: web.Application) -> None:
    root_ctx: RootContext = app["_root.context"]
    app_ctx: PrivateContext = app["logs.context"]
    app_ctx.log_cleanup_timer_evh = root_ctx.event_dispatcher.consume(
        DoLogCleanupEvent,
        app,
        log_cleanup_task,
    )
    app_ctx.log_cleanup_timer = GlobalTimer(
        root_ctx.distributed_lock_factory(LockID.LOCKID_LOG_CLEANUP_TIMER, 20.0),
        root_ctx.event_producer,
        lambda: DoLogCleanupEvent(),
        20.0,
        initial_delay=17.0,
        task_name="log_cleanup_task",
    )
    await app_ctx.log_cleanup_timer.join()


async def shutdown(app: web.Application) -> None:
    root_ctx: RootContext = app["_root.context"]
    app_ctx: PrivateContext = app["logs.context"]
    await app_ctx.log_cleanup_timer.leave()
    root_ctx.event_dispatcher.unconsume(app_ctx.log_cleanup_timer_evh)


def create_app(
    _default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    app["api_versions"] = (4, 5)
    app["prefix"] = "logs/error"
    app["logs.context"] = PrivateContext()
    return app, []
