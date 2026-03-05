"""Dependency provider for the periodic stats reporter timer.

Reports various system metrics (coroutines, agent instances, active kernels,
active users) at regular intervals.
"""

from __future__ import annotations

import asyncio
import functools
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING

import sqlalchemy as sa
import sqlalchemy.exc
from aiotools import cancel_and_wait, create_timer
from sqlalchemy.sql.expression import null, true

from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.plugin.monitor import GAUGE
from ai.backend.manager.api.utils import catch_unexpected
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.models.kernel import (
    AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    kernels,
)
from ai.backend.manager.models.keypair import keypairs

if TYPE_CHECKING:
    from ai.backend.common.plugin.monitor import StatsPluginContext
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
    from ai.backend.manager.registry import AgentRegistry

import logging

from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@catch_unexpected(log)
async def _report_stats(
    stats_monitor: StatsPluginContext,
    registry: AgentRegistry,
    db: ExtendedAsyncSAEngine,
    _interval: float,
) -> None:
    try:
        await stats_monitor.report_metric(
            GAUGE, "ai.backend.manager.coroutines", len(asyncio.all_tasks())
        )

        all_inst_ids = await registry.enumerate_instances()
        await stats_monitor.report_metric(
            GAUGE, "ai.backend.manager.agent_instances", len(all_inst_ids)
        )

        async with db.begin_readonly() as conn:
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


@dataclass
class StatsReporterInput:
    """Input required for stats reporter timer setup."""

    stats_monitor: StatsPluginContext
    registry: AgentRegistry
    db: ExtendedAsyncSAEngine


class StatsReporterDependency(
    NonMonitorableDependencyProvider[StatsReporterInput, asyncio.Task[None]]
):
    """Provides a periodic timer that reports system metrics."""

    @property
    def stage_name(self) -> str:
        return "stats-reporter"

    @asynccontextmanager
    async def provide(self, setup_input: StatsReporterInput) -> AsyncIterator[asyncio.Task[None]]:
        task = create_timer(
            functools.partial(
                _report_stats,
                setup_input.stats_monitor,
                setup_input.registry,
                setup_input.db,
            ),
            5.0,
        )
        task.set_name("stats_task")
        try:
            yield task
        finally:
            await cancel_and_wait(task)
