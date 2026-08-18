"""Types for audit log repository operations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.models.audit_log.row import AuditLogRow
from ai.backend.manager.models.audit_log.scope_row import AuditLogScopeRow
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope

__all__ = (
    "EntityAuditLogOperationScope",
    "TriggeredByAuditLogOperationScope",
)


@dataclass(frozen=True)
class EntityAuditLogOperationScope(OperationScope):
    """Audit log rows about one entity, or run within it as a scope.

    Both, because a scope action is recorded against the entities it touched while the
    scopes it ran in go to ``audit_log_scopes``. Matching only the first would hide every
    run that named this entity as its scope.

    ``existence_checks`` is empty — RBAC validation already gates entity reachability.
    """

    entity_type: RBACElementType
    entity_id: str

    @override
    def to_condition(self) -> QueryCondition:
        entity_type = self.entity_type
        entity_id = self.entity_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.or_(
                sa.and_(
                    AuditLogRow.entity_type == entity_type,
                    AuditLogRow.entity_id == entity_id,
                ),
                sa.exists().where(
                    sa.and_(
                        AuditLogScopeRow.audit_log_id == AuditLogRow.id,
                        AuditLogScopeRow.scope_type == entity_type,
                        AuditLogScopeRow.scope_id == entity_id,
                    )
                ),
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()


@dataclass(frozen=True)
class TriggeredByAuditLogOperationScope(OperationScope):
    """Audit log rows triggered by a single actor user."""

    triggered_by: str

    @override
    def to_condition(self) -> QueryCondition:
        triggered_by = self.triggered_by

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AuditLogRow.triggered_by == triggered_by

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
