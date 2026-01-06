from __future__ import annotations

from typing import TYPE_CHECKING, override

from ai.backend.manager.models.audit_log import AuditLogRow
from ai.backend.manager.repositories.base import CreatorSpec

if TYPE_CHECKING:
    from ai.backend.manager.data.audit_log.types import AuditLogData

__all__ = ("AuditLogCreatorSpec",)


class AuditLogCreatorSpec(CreatorSpec[AuditLogRow]):
    def __init__(self, data: AuditLogData) -> None:
        self._data = data

    @override
    def build_row(self) -> AuditLogRow:
        return AuditLogRow(
            action_id=self._data.action_id,
            entity_type=self._data.entity_type,
            operation=self._data.operation,
            created_at=self._data.created_at,
            description=self._data.description,
            status=self._data.status,
            entity_id=self._data.entity_id,
            request_id=self._data.request_id,
            triggered_by=self._data.triggered_by,
            duration=self._data.duration,
        )
