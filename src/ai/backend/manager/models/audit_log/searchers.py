"""Searcher implementations for the audit log repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.audit_log.types import AuditLogData, AuditLogScopeData
from ai.backend.manager.models.audit_log.row import AuditLogRow
from ai.backend.manager.models.audit_log.scope_row import AuditLogScopeRow
from ai.backend.manager.models.audit_log.searchable_fields import (
    AuditLogScopeSearchableFields,
    AuditLogSearchableFields,
)
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class AuditLogSearcher(Searcher[AuditLogRow, AuditLogData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(AuditLogRow)

    @override
    def to_data(self, row: AuditLogRow) -> AuditLogData:
        return AuditLogSearchableFields.own.to_data(row)


@dataclass
class AuditLogScopeSearcher(Searcher[AuditLogScopeRow, AuditLogScopeData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(AuditLogScopeRow)

    @override
    def to_data(self, row: AuditLogScopeRow) -> AuditLogScopeData:
        return AuditLogScopeSearchableFields.own.to_data(row)
