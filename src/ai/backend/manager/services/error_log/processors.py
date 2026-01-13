from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec

from .actions import CreateErrorLogAction, CreateErrorLogActionResult
from .actions.search import SearchErrorLogsAction, SearchErrorLogsActionResult
from .service import ErrorLogService

__all__ = ("ErrorLogProcessors",)


class ErrorLogProcessors(AbstractProcessorPackage):
    """Processor package for error log operations."""

    create: ActionProcessor[CreateErrorLogAction, CreateErrorLogActionResult]
    search: ActionProcessor[SearchErrorLogsAction, SearchErrorLogsActionResult]

    def __init__(self, service: ErrorLogService, action_monitors: list[ActionMonitor]) -> None:
        self.create = ActionProcessor(service.create, action_monitors)
        self.search = ActionProcessor(service.search, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateErrorLogAction.spec(),
            SearchErrorLogsAction.spec(),
        ]
