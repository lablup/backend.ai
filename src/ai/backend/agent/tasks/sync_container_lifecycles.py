"""Periodic task that synchronizes container lifecycles."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

from ai.backend.common.cron import PeriodicTask

if TYPE_CHECKING:
    from ai.backend.agent.agent import AbstractAgent


class SyncContainerLifecyclesTask(PeriodicTask):
    """Periodically reconcile kernel/container lifecycle state."""

    _agent: Final[AbstractAgent[Any, Any]]

    def __init__(self, agent: AbstractAgent[Any, Any]) -> None:
        self._agent = agent

    @property
    def name(self) -> str:
        return "sync_container_lifecycles"

    @property
    def interval(self) -> float:
        return self._agent.local_config.agent.sync_container_lifecycles.interval

    @property
    def initial_delay(self) -> float:
        return 0.0

    async def run(self) -> None:
        await self._agent.sync_container_lifecycles()
