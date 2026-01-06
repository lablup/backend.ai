from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.services.audit_log.actions.create import (
    CreateAuditLogAction,
    CreateAuditLogActionResult,
)

if TYPE_CHECKING:
    from ai.backend.manager.repositories.audit_log import AuditLogRepository

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AuditLogService:
    _audit_log_repository: AuditLogRepository

    def __init__(self, audit_log_repository: AuditLogRepository) -> None:
        self._audit_log_repository = audit_log_repository

    async def create(self, action: CreateAuditLogAction) -> CreateAuditLogActionResult:
        log.info("Creating audit log entry")
        data = await self._audit_log_repository.create(action.creator)
        return CreateAuditLogActionResult(audit_log_id=data.id)
