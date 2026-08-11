from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.audit_log import AUDIT_LOG_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.models.audit_log.row import AuditLogRow
from ai.backend.manager.repositories.audit_log.searchers import AuditLogSearcher


@dataclass
class SearchAuditLogsAction(SearchGlobalOpsAction[AuditLogRow, AuditLogData]):
    """Page through every audit record — the super-admin read."""

    searcher: AuditLogSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return AUDIT_LOG_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_audit_logs"

    @override
    def to_searcher(self) -> AuditLogSearcher:
        return self.searcher
