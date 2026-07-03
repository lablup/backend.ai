"""Periodic task that marks the last-access time of a proxied route."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, override

from ai.backend.common.cron import PeriodicTask

if TYPE_CHECKING:
    from ai.backend.appproxy.common.types import RouteInfo
    from ai.backend.appproxy.worker.proxy.backend.base import BaseBackend

_LAST_ACCESS_MARKER_INTERVAL: Final[float] = 1.5


class LastAccessMarkerTask(PeriodicTask):
    """Refresh the last-used-time marker for an in-flight proxied connection."""

    _backend: Final[BaseBackend]
    _route: Final[RouteInfo]

    def __init__(self, backend: BaseBackend, route: RouteInfo) -> None:
        self._backend = backend
        self._route = route

    @property
    @override
    def name(self) -> str:
        return "last_access_marker"

    @property
    @override
    def interval(self) -> float:
        return _LAST_ACCESS_MARKER_INTERVAL

    @property
    @override
    def initial_delay(self) -> float:
        return 0.0

    @override
    async def run(self) -> None:
        await self._backend.mark_last_used_time(self._route)
