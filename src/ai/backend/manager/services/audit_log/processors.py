from __future__ import annotations

from ai.backend.manager.actions.processor.bulk import BulkActionProcessor
from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import BatchOpsResult
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.services.audit_log.actions.scoped_search import (
    ScopedSearchAuditLogsAction,
    ScopedSearchAuditLogsActionResult,
)
from ai.backend.manager.services.audit_log.actions.search import SearchAuditLogsAction
from ai.backend.manager.services.audit_log.service import AuditLogService


class AuditLogProcessors:
    """The admin read runs against ops; the scoped read keeps its service.

    No create: audit rows are written by the monitors through the repository, which
    have no caller identity to gate or to record.
    """

    search: GlobalActionProcessor[SearchAuditLogsAction, BatchOpsResult[AuditLogData]]
    scoped_search: BulkActionProcessor[
        ScopedSearchAuditLogsAction, ScopedSearchAuditLogsActionResult
    ]

    def __init__(
        self,
        service: AuditLogService,
        validators: ActionValidators,
        group: ProcessorGroup[AuditLogData],
    ) -> None:
        self.search = group.global_search_ops(SearchAuditLogsAction)
        self.scoped_search = BulkActionProcessor(
            service.scoped_search,
            monitors=[],
            validators=[validators.rbac.bulk],
        )
