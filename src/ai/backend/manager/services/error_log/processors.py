from __future__ import annotations

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import BatchOpsResult, CreatedEntityOpsResult
from ai.backend.manager.data.error_log.types import ErrorLogData
from ai.backend.manager.services.error_log.actions.create import CreateErrorLogAction
from ai.backend.manager.services.error_log.actions.list import (
    ListErrorLogsAction,
    ListErrorLogsActionResult,
)
from ai.backend.manager.services.error_log.actions.mark_cleared import (
    MarkClearedErrorLogAction,
    MarkClearedErrorLogActionResult,
)
from ai.backend.manager.services.error_log.actions.search import SearchErrorLogsAction
from ai.backend.manager.services.error_log.service import ErrorLogService


class ErrorLogProcessors:
    """Recording and the admin read run against ops; the role-scoped reads keep the service."""

    create: GlobalActionProcessor[CreateErrorLogAction, CreatedEntityOpsResult[ErrorLogData]]
    search: GlobalActionProcessor[SearchErrorLogsAction, BatchOpsResult[ErrorLogData]]
    list_logs: GlobalActionProcessor[ListErrorLogsAction, ListErrorLogsActionResult]
    mark_cleared: GlobalActionProcessor[MarkClearedErrorLogAction, MarkClearedErrorLogActionResult]

    def __init__(self, service: ErrorLogService, group: ProcessorGroup[ErrorLogData]) -> None:
        self.create = group.global_create_ops(CreateErrorLogAction)
        self.search = group.global_search_ops(SearchErrorLogsAction)
        self.list_logs = group.global_scope(ListErrorLogsAction, service.list_logs)
        self.mark_cleared = group.global_scope(MarkClearedErrorLogAction, service.mark_cleared)
