from __future__ import annotations

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
    ScopedBatchOpsResult,
)
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.error_log.types import ErrorLogData
from ai.backend.manager.services.error_log.actions.create import CreateErrorLogAction
from ai.backend.manager.services.error_log.actions.delete import DeleteErrorLogAction
from ai.backend.manager.services.error_log.actions.global_search import GlobalSearchErrorLogsAction
from ai.backend.manager.services.error_log.actions.search import SearchErrorLogsAction


class ErrorLogProcessors:
    """Every operation runs against ops; the domain keeps no service of its own.

    Recording and reading are scope-shaped -- the caller acts inside the owning
    user's scope -- while clearing targets the log itself, since by then the row
    exists to name. The super-admin read spans the table and is its own action.
    """

    create: ScopeActionProcessor[CreateErrorLogAction, CreatedEntityOpsResult[ErrorLogData]]
    global_search: GlobalActionProcessor[GlobalSearchErrorLogsAction, BatchOpsResult[ErrorLogData]]
    scoped_search: ScopeActionProcessor[SearchErrorLogsAction, ScopedBatchOpsResult[ErrorLogData]]
    delete: SingleEntityActionProcessor[DeleteErrorLogAction, EntityOpsResult[ErrorLogData]]

    def __init__(self, group: ProcessorGroup[ErrorLogData]) -> None:
        self.create = group.entity_create_ops(CreateErrorLogAction)
        self.global_search = group.global_search_ops(GlobalSearchErrorLogsAction)
        self.scoped_search = group.scope_search_ops(SearchErrorLogsAction)
        self.delete = group.single_delete_ops(DeleteErrorLogAction)
