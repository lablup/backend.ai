"""Creator implementations for audit log repository."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import override

from ai.backend.manager.actions.types import OperationStatus
from ai.backend.manager.models.audit_log import AuditLogRow
from ai.backend.manager.repositories.base import CreatorSpec

__all__ = ("AuditLogCreatorSpec",)


class AuditLogCreatorSpec(CreatorSpec[AuditLogRow]):
    """Creator spec for creating an audit log entry."""

    def __init__(
        self,
        *,
        action_id: uuid.UUID,
        entity_type: str,
        operation: str,
        created_at: datetime,
        description: str,
        status: OperationStatus,
        entity_id: str | None = None,
        request_id: str | None = None,
        triggered_by: str | None = None,
        duration: timedelta | None = None,
    ) -> None:
        self._action_id = action_id
        self._entity_type = entity_type
        self._operation = operation
        self._created_at = created_at
        self._description = description
        self._status = status
        self._entity_id = entity_id
        self._request_id = request_id
        self._triggered_by = triggered_by
        self._duration = duration

    @override
    def build_row(self) -> AuditLogRow:
        return AuditLogRow(
            action_id=self._action_id,
            entity_type=self._entity_type,
            operation=self._operation,
            created_at=self._created_at,
            description=self._description,
            status=self._status,
            entity_id=self._entity_id,
            request_id=self._request_id,
            triggered_by=self._triggered_by,
            duration=self._duration,
        )
