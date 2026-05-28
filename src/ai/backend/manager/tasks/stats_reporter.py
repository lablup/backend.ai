"""Periodic task that reports manager system metrics."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Final

import sqlalchemy as sa
import sqlalchemy.exc
from sqlalchemy.sql.expression import null, true

from ai.backend.common.cron import PeriodicTask
from ai.backend.common.plugin.monitor import GAUGE
from ai.backend.logging import BraceStyleAdapter
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

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_REPORT_INTERVAL: Final[float] = 5.0


class StatsReporterTask(PeriodicTask):
    """Report system metrics (coroutines, agents, active kernels, active users)."""

    _stats_monitor: Final[StatsPluginContext]
    _registry: Final[AgentRegistry]
    _db: Final[ExtendedAsyncSAEngine]

    def __init__(
        self,
        stats_monitor: StatsPluginContext,
        registry: AgentRegistry,
        db: ExtendedAsyncSAEngine,
    ) -> None:
        self._stats_monitor = stats_monitor
        self._registry = registry
        self._db = db

    @property
    def name(self) -> str:
        return "stats_task"

    @property
    def interval(self) -> float:
        return _REPORT_INTERVAL

    @property
    def initial_delay(self) -> float:
        return 0.0

    async def run(self) -> None:
        try:
            await self._stats_monitor.report_metric(
                GAUGE, "ai.backend.manager.coroutines", len(asyncio.all_tasks())
            )

            all_inst_ids = await self._registry.enumerate_instances()
            await self._stats_monitor.report_metric(
                GAUGE, "ai.backend.manager.agent_instances", len(all_inst_ids)
            )

            async with self._db.begin_readonly() as conn:
                query = (
                    sa.select(sa.func.count())
                    .select_from(kernels)
                    .where(
                        (kernels.c.cluster_role == DEFAULT_ROLE)
                        & (kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES)),
                    )
                )
                n = await conn.scalar(query)
                await self._stats_monitor.report_metric(
                    GAUGE, "ai.backend.manager.active_kernels", n
                )
                subquery = (
                    sa.select(sa.func.count())
                    .select_from(keypairs)
                    .where(keypairs.c.is_active == true())
                    .group_by(keypairs.c.user_id)
                )
                query = sa.select(sa.func.count()).select_from(subquery.alias())
                n = await conn.scalar(query)
                await self._stats_monitor.report_metric(GAUGE, "ai.backend.users.has_active_key", n)

                subquery = subquery.where(keypairs.c.last_used != null())
                query = sa.select(sa.func.count()).select_from(subquery.alias())
                n = await conn.scalar(query)
                await self._stats_monitor.report_metric(GAUGE, "ai.backend.users.has_used_key", n)
        except (sqlalchemy.exc.InterfaceError, ConnectionRefusedError):
            log.warning("report_stats(): error while connecting to PostgreSQL server")
