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
    entity_id: str | None = None
    request_id: str | None = None
    triggered_by: str | None = None
    duration: timedelta | None = None
