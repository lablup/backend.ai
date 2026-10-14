"""BulkFieldQuerier implementations for the audit log table."""

from __future__ import annotations

from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.manager.data.audit_log.types import AuditLogData, AuditLogScopeData
from ai.backend.manager.models.audit_log.row import AuditLogRow
from ai.backend.manager.models.audit_log.scope_row import AuditLogScopeRow
from ai.backend.manager.models.audit_log.searchable_fields import (
    AuditLogScopeSearchableFields,
    AuditLogSearchableFields,
)
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
        return AuditLogSearchableFields.own.to_data(row)


class BulkAuditLogScopeQuerier(BulkFieldQuerier[AuditLogScopeRow, AuditLogScopeData]):
    """The audit record scope entries the caller named."""

    @override
    def row_class(self) -> type[AuditLogScopeRow]:
        return AuditLogScopeRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return AuditLogScopeRow.id

    @override
    def to_data(self, row: AuditLogScopeRow) -> AuditLogScopeData:
        return AuditLogScopeSearchableFields.own.to_data(row)
