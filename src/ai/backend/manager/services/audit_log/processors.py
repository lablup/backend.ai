from __future__ import annotations

from ai.backend.manager.actions.registry.field import OwnerCandidatesFieldGroup
from ai.backend.manager.actions.v2.bulk.processor import BulkActionProcessor
from ai.backend.manager.actions.v2.field.bulk_processor import (
    PartialBulkOwnerCandidatesFieldActionProcessor,
)
from ai.backend.manager.actions.v2.field.processor import NestedFieldSearchActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import BatchOpsResult, ScopedFieldsOpsResult
from ai.backend.manager.data.audit_log.types import AuditLogData, AuditLogScopeData
from ai.backend.manager.services.audit_log.actions.bulk_get import BulkGetAuditLogsAction
from ai.backend.manager.services.audit_log.actions.scoped_search import (
    ScopedSearchAuditLogsAction,
)
from ai.backend.manager.services.audit_log.actions.scoped_search_scopes import (
    ScopedSearchAuditLogScopesAction,
)
from ai.backend.manager.services.audit_log.actions.search import SearchAuditLogsAction


class AuditLogProcessors:
    """Three reads of the records kept about entities and one of the scopes nested under a
    record, all straight against ops.

    No create: audit rows are written by the monitors through the repository, which have
    no caller identity to gate or to record. A record belongs to the entity it is about,
    each scope it recorded and the user who triggered it, and is reached through any one
    of them.
    """

    global_search: GlobalActionProcessor[SearchAuditLogsAction, BatchOpsResult[AuditLogData]]
    scoped_search: BulkActionProcessor[
        ScopedSearchAuditLogsAction, ScopedFieldsOpsResult[AuditLogData]
    ]
    bulk_get: PartialBulkOwnerCandidatesFieldActionProcessor[BulkGetAuditLogsAction, AuditLogData]
    scoped_search_scopes: NestedFieldSearchActionProcessor[
        ScopedSearchAuditLogScopesAction, ScopedFieldsOpsResult[AuditLogScopeData]
    ]

    def __init__(self, group: OwnerCandidatesFieldGroup[AuditLogData]) -> None:
        self.global_search = group.global_searcher_ops(SearchAuditLogsAction)
        self.scoped_search = group.atomic_bulk_scoped_search_ops(ScopedSearchAuditLogsAction)
        self.bulk_get = group.partial_bulk_get_ops(BulkGetAuditLogsAction)
        self.scoped_search_scopes = group.nested_field_search_ops(
            ScopedSearchAuditLogScopesAction, AuditLogScopeData
        )
