from __future__ import annotations

from ai.backend.manager.actions.registry import FieldProcessorGroup
from ai.backend.manager.actions.v2.field.processor import SingleFieldActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedFieldOpsResult,
    EntityOpsResult,
    ScopedFieldsOpsResult,
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

    A log is a field row of the user it happened to: recording one is answered for by
    that user, and so is clearing it. The super-admin read spans the table.
    """

    create: SingleEntityActionProcessor[CreateErrorLogAction, CreatedFieldOpsResult[ErrorLogData]]
    global_search: GlobalActionProcessor[GlobalSearchErrorLogsAction, BatchOpsResult[ErrorLogData]]
    scoped_search: ScopeActionProcessor[SearchErrorLogsAction, ScopedFieldsOpsResult[ErrorLogData]]
    delete: SingleFieldActionProcessor[DeleteErrorLogAction, EntityOpsResult[ErrorLogData]]

    def __init__(self, logs: FieldProcessorGroup[ErrorLogData]) -> None:
        self.create = logs.create_ops(CreateErrorLogAction)
        self.global_search = logs.global_search_ops(GlobalSearchErrorLogsAction)
        self.scoped_search = logs.search_ops(SearchErrorLogsAction)
        self.delete = logs.delete_ops(DeleteErrorLogAction)
