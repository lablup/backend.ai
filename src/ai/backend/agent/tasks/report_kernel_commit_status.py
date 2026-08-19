"""Periodic task that reports kernel commit statuses."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, override

from ai.backend.common.cron import PeriodicTask

if TYPE_CHECKING:
    from ai.backend.agent.agent import AbstractAgent

_REPORT_COMMIT_STATUS_INTERVAL: Final[float] = 7.0


class ReportKernelCommitStatusTask(PeriodicTask):
    """Periodically scan and report ongoing kernel commit statuses."""

    _agent: Final[AbstractAgent[Any, Any]]

    def __init__(self, agent: AbstractAgent[Any, Any]) -> None:
        self._agent = agent

    @property
    @override
    def name(self) -> str:
        return "report_kernel_commit_status"

    @property
    @override
    def interval(self) -> float:
        return _REPORT_COMMIT_STATUS_INTERVAL

    @property
    @override
    def initial_delay(self) -> float:
        return 0.0

    @override
    async def run(self) -> None:
        await self._agent.report_all_kernel_commit_status_map()
