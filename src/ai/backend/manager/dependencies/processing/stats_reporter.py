"""Dependency provider for the periodic stats reporter timer.

Reports various system metrics (coroutines, agent instances, active kernels,
active users) at regular intervals.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from ai.backend.common.cron import LocalCron
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.manager.tasks.stats_reporter import StatsReporterTask

if TYPE_CHECKING:
    from ai.backend.common.plugin.monitor import StatsPluginContext
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
    from ai.backend.manager.registry import AgentRegistry


@dataclass
class StatsReporterInput:
    """Input required for stats reporter timer setup."""

    stats_monitor: StatsPluginContext
    registry: AgentRegistry
    db: ExtendedAsyncSAEngine


class StatsReporterDependency(NonMonitorableDependencyProvider[StatsReporterInput, LocalCron]):
    """Provides a periodic timer that reports system metrics."""

    @property
    @override
    def stage_name(self) -> str:
        return "stats-reporter"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: StatsReporterInput) -> AsyncIterator[LocalCron]:
        cron = LocalCron([
            StatsReporterTask(
                setup_input.stats_monitor,
                setup_input.registry,
                setup_input.db,
            )
        ])
        await cron.start()
        try:
            yield cron
        finally:
            await cron.stop()
