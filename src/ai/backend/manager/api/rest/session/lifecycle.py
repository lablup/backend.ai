"""Session sub-app lifecycle hooks.

Extracted from the legacy ``api/session.py`` module so that the
``rest/session`` package owns its own startup/shutdown concerns.
"""

from __future__ import annotations

import asyncio
import functools
import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import aiotools
import attrs
import sqlalchemy as sa
import sqlalchemy.exc
from aiohttp import web
from aiotools import cancel_and_wait
from dateutil.tz import tzutc
from sqlalchemy.sql.expression import null, true

from ai.backend.common.events.event_types.agent.anycast import AgentTerminatedEvent
from ai.backend.common.plugin.monitor import GAUGE
from ai.backend.common.types import AgentId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.utils import catch_unexpected
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.models.kernel import (
    AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    kernels,
)
from ai.backend.manager.models.keypair import keypairs

if TYPE_CHECKING:
    from ai.backend.manager.api.context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@catch_unexpected(log)
async def check_agent_lost(root_ctx: RootContext, _interval: float) -> None:
    try:
        now = datetime.now(tzutc())
        timeout = timedelta(seconds=root_ctx.config_provider.config.manager.heartbeat_timeout)

        agent_last_seen = await root_ctx.valkey_live.scan_agent_last_seen()
        for agent_id, prev_timestamp in agent_last_seen:
            prev = datetime.fromtimestamp(prev_timestamp, tzutc())
            if now - prev > timeout:
                await root_ctx.event_producer.anycast_event(
                    AgentTerminatedEvent("agent-lost"),
                    source_override=AgentId(agent_id),
                )
    except asyncio.CancelledError:
        pass


@catch_unexpected(log)
async def report_stats(root_ctx: RootContext, _interval: float) -> None:
    try:
        stats_monitor = root_ctx.stats_monitor
        await stats_monitor.report_metric(
            GAUGE, "ai.backend.manager.coroutines", len(asyncio.all_tasks())
        )

        all_inst_ids = await root_ctx.registry.enumerate_instances()
        await stats_monitor.report_metric(
            GAUGE, "ai.backend.manager.agent_instances", len(all_inst_ids)
        )

        async with root_ctx.db.begin_readonly() as conn:
            query = (
                sa.select(sa.func.count())
                .select_from(kernels)
                .where(
                    (kernels.c.cluster_role == DEFAULT_ROLE)
                    & (kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES)),
                )
            )
            n = await conn.scalar(query)
            await stats_monitor.report_metric(GAUGE, "ai.backend.manager.active_kernels", n)
            subquery = (
                sa.select(sa.func.count())
                .select_from(keypairs)
                .where(keypairs.c.is_active == true())
                .group_by(keypairs.c.user_id)
            )
            query = sa.select(sa.func.count()).select_from(subquery.alias())
            n = await conn.scalar(query)
            await stats_monitor.report_metric(GAUGE, "ai.backend.users.has_active_key", n)

            subquery = subquery.where(keypairs.c.last_used != null())
            query = sa.select(sa.func.count()).select_from(subquery.alias())
            n = await conn.scalar(query)
            await stats_monitor.report_metric(GAUGE, "ai.backend.users.has_used_key", n)
    except (sqlalchemy.exc.InterfaceError, ConnectionRefusedError):
        log.warning("report_stats(): error while connecting to PostgreSQL server")


@attrs.define(slots=True, auto_attribs=True, init=False)
class PrivateContext:
    agent_lost_checker: asyncio.Task[None]
    stats_task: asyncio.Task[None]
    database_ptask_group: aiotools.PersistentTaskGroup
    rpc_ptask_group: aiotools.PersistentTaskGroup
    webhook_ptask_group: aiotools.PersistentTaskGroup


async def init(app: web.Application) -> None:
    root_ctx: RootContext = app["_root.context"]
    app_ctx: PrivateContext = app["session.context"]
    app_ctx.database_ptask_group = aiotools.PersistentTaskGroup()
    app_ctx.rpc_ptask_group = aiotools.PersistentTaskGroup()
    app_ctx.webhook_ptask_group = aiotools.PersistentTaskGroup()

    app_ctx.agent_lost_checker = aiotools.create_timer(
        functools.partial(check_agent_lost, root_ctx), 1.0
    )
    app_ctx.agent_lost_checker.set_name("agent_lost_checker")
    app_ctx.stats_task = aiotools.create_timer(
        functools.partial(report_stats, root_ctx),
        5.0,
    )
    app_ctx.stats_task.set_name("stats_task")


async def shutdown(app: web.Application) -> None:
    app_ctx: PrivateContext = app["session.context"]
    await cancel_and_wait(app_ctx.agent_lost_checker)
    await cancel_and_wait(app_ctx.stats_task)

    await app_ctx.webhook_ptask_group.shutdown()
    await app_ctx.database_ptask_group.shutdown()
    await app_ctx.rpc_ptask_group.shutdown()
