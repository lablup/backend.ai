from collections.abc import Awaitable, Callable, Sequence

from ai.backend.manager.actions.action import BaseAction, BaseActionResult
from ai.backend.manager.actions.monitors.monitor import ActionMonitor

from .base import ActionProcessor


class MonitorFilteredActionProcessorFactory:
    _monitors: Sequence[ActionMonitor] | None
    _monitor_types_to_exclude: set[type[ActionMonitor]]

    def __init__(
        self,
        monitors: Sequence[ActionMonitor] | None = None,
        monitor_types_to_exclude: set[type[ActionMonitor]] | None = None,
    ) -> None:
        self._monitors = monitors
        self._monitor_types_to_exclude = monitor_types_to_exclude or set()

    def _build_monitors(self) -> list[ActionMonitor]:
        monitors: list[ActionMonitor] = []
        for monitor in self._monitors or []:
            if type(monitor) in self._monitor_types_to_exclude:
                continue
            monitors.append(monitor)
        return monitors

    def build[TAction: BaseAction, TActionResult: BaseActionResult](
        self,
        func: Callable[[TAction], Awaitable[TActionResult]],
    ) -> ActionProcessor[TAction, TActionResult]:
        monitors = self._build_monitors()
        return ActionProcessor(func, monitors)
