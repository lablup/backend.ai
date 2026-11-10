from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.audit_log import AuditLogScopeID
from ai.backend.manager.actions.v2.field.ops import PartialBulkGetOwnerCandidatesFieldOpsAction
from ai.backend.manager.data.audit_log.types import AuditLogScopeData
from ai.backend.manager.models.audit_log.queriers import BulkAuditLogScopeQuerier
from ai.backend.manager.models.audit_log.scope_row import AuditLogScopeRow


@dataclass
class BulkGetAuditLogScopesAction(
    PartialBulkGetOwnerCandidatesFieldOpsAction[
        AuditLogScopeID, AuditLogScopeRow, AuditLogScopeData
    ]
):
    """Read the scope entries the caller named, each reached through any one of its
    record's owners."""

    ids: Sequence[AuditLogScopeID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_audit_log_scopes"

    @override
    def field_ids(self) -> Sequence[AuditLogScopeID]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkAuditLogScopeQuerier:
        return BulkAuditLogScopeQuerier()

    @override
    def narrowed_to(self, field_ids: Sequence[AuditLogScopeID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(self, ids=[field_id for field_id in self.ids if field_id in allowed])
