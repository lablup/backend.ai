"""Periodic task that collects per-node and per-device statistics."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from ai.backend.common.cron import PeriodicTask
from ai.backend.common.metrics.types import UTILIZATION_METRIC_INTERVAL

if TYPE_CHECKING:
    from ai.backend.agent.runtime import AgentRuntime


class CollectNodeStatTask(PeriodicTask):
    """Periodically trigger node/device statistics collection for all agents."""

    _runtime: Final[AgentRuntime]

    def __init__(self, runtime: AgentRuntime) -> None:
        self._runtime = runtime

    @property
    def name(self) -> str:
        return "collect_node_stat"

    @property
    def interval(self) -> float:
        return UTILIZATION_METRIC_INTERVAL

    @property
    def initial_delay(self) -> float:
        return 0.0

    async def run(self) -> None:
        await self._runtime.collect_node_stats()
