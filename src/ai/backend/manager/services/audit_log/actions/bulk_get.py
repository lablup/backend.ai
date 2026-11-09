from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.audit_log import AuditLogID
from ai.backend.manager.actions.v2.field.ops import PartialBulkGetOwnerCandidatesFieldOpsAction
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.models.audit_log.queriers import BulkAuditLogQuerier
from ai.backend.manager.models.audit_log.row import AuditLogRow


@dataclass
class BulkGetAuditLogsAction(
    PartialBulkGetOwnerCandidatesFieldOpsAction[AuditLogID, AuditLogRow, AuditLogData]
):
    """Read the audit records the caller named, each reached through any one of its
    owners."""

    ids: Sequence[AuditLogID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_audit_logs"

    @override
    def field_ids(self) -> Sequence[AuditLogID]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkAuditLogQuerier:
        return BulkAuditLogQuerier()

    @override
    def narrowed_to(self, field_ids: Sequence[AuditLogID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(self, ids=[field_id for field_id in self.ids if field_id in allowed])
