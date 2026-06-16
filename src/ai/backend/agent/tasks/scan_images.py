"""Periodic task that rescans installed images on the agent."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

from ai.backend.common.cron import PeriodicTask

if TYPE_CHECKING:
    from ai.backend.agent.agent import AbstractAgent

_SCAN_IMAGES_INTERVAL: Final[float] = 20.0


class ScanImagesTask(PeriodicTask):
    """Periodically rescan installed images and emit removal events."""

    _agent: Final[AbstractAgent[Any, Any]]

    def __init__(self, agent: AbstractAgent[Any, Any]) -> None:
        self._agent = agent

    @property
    def name(self) -> str:
        return "scan_images"

    @property
    def interval(self) -> float:
        return _SCAN_IMAGES_INTERVAL

    @property
    def initial_delay(self) -> float:
        return 0.0

    async def run(self) -> None:
        await self._agent.scan_images_periodically()
