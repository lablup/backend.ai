from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import override

from ai.backend.manager.actions.types import OperationStatus
from ai.backend.manager.models.audit_log import AuditLogRow
from ai.backend.manager.repositories.base import CreatorSpec

__all__ = ("AuditLogCreatorSpec",)


@dataclass
class AuditLogCreatorSpec(CreatorSpec[AuditLogRow]):
    action_id: uuid.UUID
    entity_type: str
    operation: str
    created_at: datetime
    description: str
    status: OperationStatus
    entity_id: str | None
    request_id: str | None
    triggered_by: str | None
    duration: timedelta | None

    @override
    def build_row(self) -> AuditLogRow:
        return AuditLogRow(
            action_id=self.action_id,
            entity_type=self.entity_type,
            operation=self.operation,
            created_at=self.created_at,
            description=self.description,
            status=self.status,
            entity_id=self.entity_id,
            request_id=self.request_id,
            triggered_by=self.triggered_by,
            duration=self.duration,
        )
