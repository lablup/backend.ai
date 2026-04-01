from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators

from .actions import CreateErrorLogAction, CreateErrorLogActionResult
from .actions.list import ListErrorLogsAction, ListErrorLogsActionResult
from .actions.mark_cleared import MarkClearedErrorLogAction, MarkClearedErrorLogActionResult
from .actions.search import SearchErrorLogsAction, SearchErrorLogsActionResult
from .service import ErrorLogService

__all__ = ("ErrorLogProcessors",)


class ErrorLogProcessors(AbstractProcessorPackage):
    """Processor package for error log operations."""

    create: ActionProcessor[CreateErrorLogAction, CreateErrorLogActionResult]
    search: ActionProcessor[SearchErrorLogsAction, SearchErrorLogsActionResult]
    list_logs: ActionProcessor[ListErrorLogsAction, ListErrorLogsActionResult]
    mark_cleared: ActionProcessor[MarkClearedErrorLogAction, MarkClearedErrorLogActionResult]

    def __init__(
        self,
        service: ErrorLogService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        self.create = ActionProcessor(service.create, action_monitors)
        self.search = ActionProcessor(service.search, action_monitors)
        self.list_logs = ActionProcessor(service.list_logs, action_monitors)
        self.mark_cleared = ActionProcessor(service.mark_cleared, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateErrorLogAction.spec(),
            SearchErrorLogsAction.spec(),
            ListErrorLogsAction.spec(),
            MarkClearedErrorLogAction.spec(),
        ]
