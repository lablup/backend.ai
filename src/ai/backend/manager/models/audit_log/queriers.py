"""BulkFieldQuerier implementations for the audit log table."""

from __future__ import annotations

from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.models.audit_log.row import AuditLogRow
from ai.backend.manager.models.specs.querier import BulkFieldQuerier


class BulkAuditLogQuerier(BulkFieldQuerier[AuditLogRow, AuditLogData]):
    """The audit records the caller named."""

    @override
    def row_class(self) -> type[AuditLogRow]:
        return AuditLogRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return AuditLogRow.id

    @override
    def to_data(self, row: AuditLogRow) -> AuditLogData:
        return row.to_dataclass()
