"""Audit-log search over the entities it reads the records of."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import final, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import BulkScopedSearchOpsAction
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.models.audit_log.row import AuditLogRow
from ai.backend.manager.models.audit_log.scopes import AuditLogTarget
from ai.backend.manager.models.audit_log.searchers import AuditLogSearcher
from ai.backend.manager.models.scopes import OperationScope


@dataclass
class ScopedSearchAuditLogsAction(BulkScopedSearchOpsAction[AuditLogRow, AuditLogData]):
    """Page through the records of the entities named, combined with OR.

    Every entity is authorized before the read runs, so a caller reaching for one they
    cannot see is refused rather than served the rest.
    """

    targets: Sequence[AuditLogTarget]
    searcher: AuditLogSearcher

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_audit_logs"

    @final
    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return [target.scope_id() for target in self.targets]

    @final
    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return self.targets

    @override
    def to_searcher(self) -> AuditLogSearcher:
        return self.searcher
