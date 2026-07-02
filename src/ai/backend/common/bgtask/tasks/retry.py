"""Periodic task that retries unmanaged background tasks."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, override

from ai.backend.common.cron import PeriodicTask

if TYPE_CHECKING:
    from ai.backend.common.bgtask.bgtask import BackgroundTaskManager

_RETRY_CHECK_INTERVAL: Final[float] = 300.0


class BgtaskRetryTask(PeriodicTask):
    """Periodically scan for stale/failed background tasks and revive them."""

    _manager: Final[BackgroundTaskManager]

    def __init__(self, manager: BackgroundTaskManager) -> None:
        self._manager = manager

    @property
    @override
    def name(self) -> str:
        return "bgtask_retry"

    @property
    @override
    def interval(self) -> float:
        return _RETRY_CHECK_INTERVAL

    @property
    @override
    def initial_delay(self) -> float:
        return 0.0

    @override
    async def run(self) -> None:
        await self._manager.do_retry_check()
