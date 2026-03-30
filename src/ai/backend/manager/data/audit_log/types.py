from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from ai.backend.manager.actions.types import OperationStatus


@dataclass
class AuditLogData:
    id: uuid.UUID
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


@dataclass
class AuditLogListResult:
    """Search result with total count and pagination info for audit logs."""

    items: list[AuditLogData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
