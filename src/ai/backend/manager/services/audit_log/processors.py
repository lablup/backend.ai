from __future__ import annotations

from ai.backend.manager.actions.registry.field import FieldGroup
from ai.backend.manager.actions.v2.bulk.processor import BulkActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import BatchOpsResult, ScopedFieldsOpsResult
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.services.audit_log.actions.scoped_search import (
    ScopedSearchAuditLogsAction,
)
from ai.backend.manager.services.audit_log.actions.search import SearchAuditLogsAction


class AuditLogProcessors:
    """Two reads of the records kept about entities, both straight against ops.

    No create: audit rows are written by the monitors through the repository, which have
    no caller identity to gate or to record. A record is a field of whatever entity the
    action was about, so the owned read names those entities and the global one names
    none.
    """

    global_search: GlobalActionProcessor[SearchAuditLogsAction, BatchOpsResult[AuditLogData]]
    scoped_search: BulkActionProcessor[
        ScopedSearchAuditLogsAction, ScopedFieldsOpsResult[AuditLogData]
    ]

    def __init__(self, group: FieldGroup[AuditLogData]) -> None:
        self.global_search = group.global_search_ops(SearchAuditLogsAction)
        self.scoped_search = group.bulk_scoped_search_ops(ScopedSearchAuditLogsAction)
