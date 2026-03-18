from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.audit_log import AuditLogRow
from ai.backend.manager.repositories.base import Creator
from ai.backend.manager.services.audit_log.actions.base import AuditLogAction


@dataclass
class CreateAuditLogAction(AuditLogAction):
    creator: Creator[AuditLogRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateAuditLogActionResult(BaseActionResult):
    audit_log_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.audit_log_id)
