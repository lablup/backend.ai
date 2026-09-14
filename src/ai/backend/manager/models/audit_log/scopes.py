"""Operation scopes for audit logs."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.models.audit_log.row import AuditLogRow
from ai.backend.manager.models.audit_log.scope_row import AuditLogScopeRow
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope

__all__ = (
    "EntityAuditLogOperationScope",
    "ScopeAuditLogOperationScope",
    "TriggeredByAuditLogOperationScope",
)


@dataclass(frozen=True)
class EntityAuditLogOperationScope(OperationScope):
    """The records about one entity: the run named it as what it touched.

    ``existence_checks`` is empty -- RBAC validation already gates entity reachability.
    """

    entity_type: EntityType
    entity_id: str

    @override
    def to_condition(self) -> QueryCondition:
        entity_type = self.entity_type
        entity_id = self.entity_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                AuditLogRow.entity_type == entity_type,
                AuditLogRow.entity_id == entity_id,
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()


@dataclass(frozen=True)
class ScopeAuditLogOperationScope(OperationScope):
    """The records of the runs that named one entity as the scope they ran in.

    The other half of what an entity's history means, kept apart so a caller asks for
    one or the other rather than always both: a scope action records the entities it
    touched on the row and the scopes it ran in on ``audit_log_scopes``.
    """

    entity_type: EntityType
    entity_id: str

    @override
    def to_condition(self) -> QueryCondition:
        entity_type = self.entity_type
        entity_id = self.entity_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.exists().where(
                sa.and_(
                    AuditLogScopeRow.audit_log_id == AuditLogRow.id,
                    AuditLogScopeRow.scope_type == entity_type,
                    AuditLogScopeRow.scope_id == entity_id,
                )
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
