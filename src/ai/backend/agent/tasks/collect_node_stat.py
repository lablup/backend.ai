"""Periodic task that collects per-node and per-device statistics."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from ai.backend.common.cron import PeriodicTask

if TYPE_CHECKING:
    from ai.backend.agent.config.unified import AgentUnifiedConfig
    from ai.backend.agent.runtime import AgentRuntime


class CollectNodeStatTask(PeriodicTask):
    """Periodically trigger node/device statistics collection for all agents."""

    _runtime: Final[AgentRuntime]
    _local_config: Final[AgentUnifiedConfig]

    def __init__(self, runtime: AgentRuntime, local_config: AgentUnifiedConfig) -> None:
        self._runtime = runtime
        self._local_config = local_config

    @property
    def name(self) -> str:
        return "collect_node_stat"

    @property
    def interval(self) -> float:
        return self._local_config.agent.utilization_metric.node.interval

    @property
    def initial_delay(self) -> float:
        return 0.0

    async def run(self) -> None:
        await self._runtime.collect_node_stats()
