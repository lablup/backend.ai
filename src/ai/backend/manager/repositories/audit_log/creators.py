from __future__ import annotations

from typing import TYPE_CHECKING, override

from ai.backend.manager.models.audit_log import AuditLogRow
from ai.backend.manager.repositories.base import CreatorSpec

if TYPE_CHECKING:
    from ai.backend.manager.data.audit_log.types import AuditLogData

__all__ = ("AuditLogCreatorSpec",)


class AuditLogCreatorSpec(CreatorSpec[AuditLogRow]):
    def __init__(self, data: AuditLogData) -> None:
        self._action_id = data.action_id
        self._entity_type = data.entity_type
        self._operation = data.operation
        self._created_at = data.created_at
        self._description = data.description
        self._status = data.status
        self._entity_id = data.entity_id
        self._request_id = data.request_id
        self._triggered_by = data.triggered_by
        self._duration = data.duration

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
