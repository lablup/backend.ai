from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import final, override

from ai.backend.common.data.entity.audit_log import AuditLogID
from ai.backend.manager.actions.v2.field.ops import NestedFieldSearchOpsAction
from ai.backend.manager.data.audit_log.types import AuditLogScopeData
from ai.backend.manager.models.audit_log.scope_row import AuditLogScopeRow
from ai.backend.manager.models.audit_log.scopes import AuditLogIDScope
from ai.backend.manager.models.audit_log.searchers import AuditLogScopeSearcher
from ai.backend.manager.models.scopes import OperationScope


@dataclass
class ScopedSearchAuditLogScopesAction(
    NestedFieldSearchOpsAction[AuditLogID, AuditLogScopeRow, AuditLogScopeData]
):
    """Page through the scopes nested under one record."""

    audit_log_id: AuditLogID
    searcher: AuditLogScopeSearcher

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_audit_log_scopes"

    @override
    def field_id(self) -> AuditLogID:
        return self.audit_log_id

    @final
    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [AuditLogIDScope(audit_log_id=self.audit_log_id)]

    @override
    def to_searcher(self) -> AuditLogScopeSearcher:
        return self.searcher
