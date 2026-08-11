from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.services.audit_log.actions.scoped_search import (
    ScopedSearchAuditLogsAction,
    ScopedSearchAuditLogsActionResult,
)

if TYPE_CHECKING:
    from ai.backend.manager.repositories.audit_log import AuditLogRepository

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AuditLogService:
    _audit_log_repository: AuditLogRepository

    def __init__(self, audit_log_repository: AuditLogRepository) -> None:
        self._audit_log_repository = audit_log_repository

    async def scoped_search(
        self, action: ScopedSearchAuditLogsAction
    ) -> ScopedSearchAuditLogsActionResult:
        targets = list(action.targets())
        scopes = [t.to_search_scope() for t in targets]
        result = await self._audit_log_repository.scoped_search(action.querier, scopes)
        return ScopedSearchAuditLogsActionResult(
            data=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            queried_refs=[t.to_rbac_element_ref() for t in targets],
        )
