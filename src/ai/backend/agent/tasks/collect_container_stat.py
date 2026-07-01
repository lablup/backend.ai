"""Periodic task that collects per-container statistics."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

from ai.backend.common.cron import PeriodicTask

if TYPE_CHECKING:
    from ai.backend.agent.agent import AbstractAgent
    from ai.backend.agent.config.unified import AgentUnifiedConfig


class CollectContainerStatTask(PeriodicTask):
    """Periodically trigger the agent's per-container statistics collection."""

    _agent: Final[AbstractAgent[Any, Any]]
    _local_config: Final[AgentUnifiedConfig]

    def __init__(self, agent: AbstractAgent[Any, Any], local_config: AgentUnifiedConfig) -> None:
        self._agent = agent
        self._local_config = local_config

    @property
    def name(self) -> str:
        return "collect_container_stat"

    @property
    def interval(self) -> float:
        return self._local_config.agent.utilization_metric.container.interval

    @property
    def initial_delay(self) -> float:
        return 0.0

    async def run(self) -> None:
        await self._agent.collect_container_stat()
