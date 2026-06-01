"""Periodic task that collects per-process statistics inside containers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

from ai.backend.common.cron import PeriodicTask
from ai.backend.common.metrics.types import UTILIZATION_METRIC_INTERVAL

if TYPE_CHECKING:
    from ai.backend.agent.agent import AbstractAgent


class CollectProcessStatTask(PeriodicTask):
    """Periodically trigger the agent's per-process statistics collection."""

    _agent: Final[AbstractAgent[Any, Any]]

    def __init__(self, agent: AbstractAgent[Any, Any]) -> None:
        self._agent = agent

    @property
    def name(self) -> str:
        return "collect_process_stat"

    @property
    def interval(self) -> float:
        return UTILIZATION_METRIC_INTERVAL

    @property
    def initial_delay(self) -> float:
        return 0.0

    async def run(self) -> None:
        await self._agent.collect_process_stat()
