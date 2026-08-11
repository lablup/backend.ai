from __future__ import annotations

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import BatchOpsResult, CreatedEntityOpsResult
from ai.backend.manager.data.error_log.types import ErrorLogData
from ai.backend.manager.services.error_log.actions.admin_search import AdminSearchErrorLogsAction
from ai.backend.manager.services.error_log.actions.create import CreateErrorLogAction
from ai.backend.manager.services.error_log.actions.mark_cleared import (
    MarkClearedErrorLogAction,
    MarkClearedErrorLogActionResult,
)
from ai.backend.manager.services.error_log.actions.search import (
    SearchErrorLogsAction,
    SearchErrorLogsActionResult,
)
from ai.backend.manager.services.error_log.service import ErrorLogService


class ErrorLogProcessors:
    """Recording and the admin read run against ops; the role-scoped reads keep the service."""

    create: GlobalActionProcessor[CreateErrorLogAction, CreatedEntityOpsResult[ErrorLogData]]
    search: GlobalActionProcessor[AdminSearchErrorLogsAction, BatchOpsResult[ErrorLogData]]
    list_logs: GlobalActionProcessor[SearchErrorLogsAction, SearchErrorLogsActionResult]
    mark_cleared: GlobalActionProcessor[MarkClearedErrorLogAction, MarkClearedErrorLogActionResult]

    def __init__(self, service: ErrorLogService, group: ProcessorGroup[ErrorLogData]) -> None:
        self.create = group.global_create_ops(CreateErrorLogAction)
        self.search = group.global_search_ops(AdminSearchErrorLogsAction)
        self.list_logs = group.global_scope(SearchErrorLogsAction, service.list_logs)
        self.mark_cleared = group.global_scope(MarkClearedErrorLogAction, service.mark_cleared)
