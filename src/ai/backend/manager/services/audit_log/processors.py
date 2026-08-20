from __future__ import annotations

from ai.backend.manager.actions.registry.sidecar import SidecarProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import BatchOpsResult, ScopedFieldsOpsResult
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.services.audit_log.actions.scoped_search import (
    ScopedSearchAuditLogsAction,
)
from ai.backend.manager.services.audit_log.actions.search import SearchAuditLogsAction


class AuditLogProcessors:
    """Two reads of rows that ride beside the graph, both straight against ops.

    No create: audit rows are written by the monitors through the repository, which have
    no caller identity to gate or to record. Neither read reports an entity — an audit
    row is not one; the entities a scoped read stayed within are on its scope targets.
    """

    global_search: GlobalActionProcessor[SearchAuditLogsAction, BatchOpsResult[AuditLogData]]
    scoped_search: ScopeActionProcessor[
        ScopedSearchAuditLogsAction, ScopedFieldsOpsResult[AuditLogData]
    ]

    def __init__(self, group: SidecarProcessorGroup[AuditLogData]) -> None:
        self.global_search = group.global_search_ops(SearchAuditLogsAction)
        self.scoped_search = group.search_ops(ScopedSearchAuditLogsAction)
