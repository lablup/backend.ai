from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.services.audit_log.actions.create import (
    CreateAuditLogAction,
    CreateAuditLogActionResult,
)
from ai.backend.manager.services.audit_log.actions.search import (
    SearchAuditLogsAction,
    SearchAuditLogsActionResult,
)

if TYPE_CHECKING:
    from ai.backend.manager.repositories.audit_log import AuditLogRepository

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AuditLogService:
    _audit_log_repository: AuditLogRepository

    def __init__(self, audit_log_repository: AuditLogRepository) -> None:
        self._audit_log_repository = audit_log_repository

    async def create(self, action: CreateAuditLogAction) -> CreateAuditLogActionResult:
        data = await self._audit_log_repository.create(action.creator)
        return CreateAuditLogActionResult(audit_log_id=data.id)

    async def search(self, action: SearchAuditLogsAction) -> SearchAuditLogsActionResult:
        result = await self._audit_log_repository.search(action.querier)
        return SearchAuditLogsActionResult(
            data=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
