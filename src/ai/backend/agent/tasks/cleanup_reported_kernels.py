"""Periodic task that cleans up abuse-reported kernels."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, override

from ai.backend.common.cron import PeriodicTask

if TYPE_CHECKING:
    from ai.backend.agent.agent import AbstractAgent

_CLEANUP_REPORTED_KERNELS_INTERVAL: Final[float] = 30.0


class CleanupReportedKernelsTask(PeriodicTask):
    """Periodically clean up kernels reported as abnormal by the Watcher."""

    _agent: Final[AbstractAgent[Any, Any]]

    def __init__(self, agent: AbstractAgent[Any, Any]) -> None:
        self._agent = agent

    @property
    @override
    def name(self) -> str:
        return "cleanup_reported_kernels"

    @property
    @override
    def interval(self) -> float:
        return _CLEANUP_REPORTED_KERNELS_INTERVAL

    @property
    @override
    def initial_delay(self) -> float:
        return 0.0

    @override
    async def run(self) -> None:
        await self._agent.cleanup_reported_kernels()
