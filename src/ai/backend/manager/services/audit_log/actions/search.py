from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityType, GlobalEntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.models.audit_log.row import AuditLogRow


@dataclass(frozen=True)
class SearchAuditLogsAction(GlobalSearcherOpsAction[AuditLogRow, AuditLogData]):
    """Page through every audit record — the super-admin read."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return GlobalEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_audit_logs"
