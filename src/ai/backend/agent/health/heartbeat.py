"""Periodic task that sends agent heartbeats to the manager."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

from ai.backend.common.cron import PeriodicTask

if TYPE_CHECKING:
    from ai.backend.agent.agent import AbstractAgent


class HeartbeatTask(PeriodicTask):
    """Periodically send the agent's status and image list to the manager."""

    _agent: Final[AbstractAgent[Any, Any]]

    def __init__(self, agent: AbstractAgent[Any, Any]) -> None:
        self._agent = agent

    @property
    def name(self) -> str:
        return "heartbeat"

    @property
    def interval(self) -> float:
        return self._agent.local_config.debug.heartbeat_interval

    @property
    def initial_delay(self) -> float:
        return 0.0

    async def run(self) -> None:
        await self._agent.heartbeat()
