from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import override

from ai.backend.common.data.entity.action import ActionID
from ai.backend.common.data.entity.audit_log import AuditLogID
from ai.backend.common.data.entity.types import EntityData, EntityID, EntityIdentifier
from ai.backend.manager.actions.types import ActionKind, OperationStatus


@dataclass
class AuditLogData(EntityData):
    """One audit record, mirroring the row.

    ``action_kind`` says which shape wrote it; only that shape's target columns are
    set. ``id`` is this record; ``target_entity_id`` is what it is about.
    """

    id: AuditLogID
    action_id: ActionID
    action_kind: ActionKind | None
    action_name: str
    entity_type: str
    operation: str
    created_at: datetime
    description: str
    status: OperationStatus
    target_entity_id: str | None
    lookup_kind: str | None
    lookup_key: str | None
    request_id: str | None
    triggered_by: str | None
    acted_as: uuid.UUID | None
    duration: timedelta | None

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.id


@dataclass
class AuditLogListResult:
    """Search result with total count and pagination info for audit logs."""

    items: list[AuditLogData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
