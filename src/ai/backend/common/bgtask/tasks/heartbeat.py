"""Periodic task that publishes heartbeats for ongoing background tasks."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from ai.backend.common.cron import PeriodicTask

if TYPE_CHECKING:
    from ai.backend.common.bgtask.bgtask import BackgroundTaskManager

_HEARTBEAT_INTERVAL: Final[float] = 60.0


class BgtaskHeartbeatTask(PeriodicTask):
    """Periodically refresh the heartbeat for ongoing background tasks."""

    _manager: Final[BackgroundTaskManager]

    def __init__(self, manager: BackgroundTaskManager) -> None:
        self._manager = manager

    @property
    def name(self) -> str:
        return "bgtask_heartbeat"

    @property
    def interval(self) -> float:
        return _HEARTBEAT_INTERVAL

    @property
    def initial_delay(self) -> float:
        return 0.0

    async def run(self) -> None:
        await self._manager.do_heartbeat()
