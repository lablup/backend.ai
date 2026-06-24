"""Types for audit log repository operations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.models.audit_log import AuditLogRow
from ai.backend.manager.models.query_types import QueryCondition
from ai.backend.manager.repositories.base import ExistenceCheck, SearchScope

__all__ = (
    "EntityAuditLogSearchScope",
    "TriggeredByAuditLogSearchScope",
)


@dataclass(frozen=True)
class EntityAuditLogSearchScope(SearchScope):
    """Audit log rows tagged with one ``(entity_type, entity_id)`` pair.

    One scope = one item of a scoped audit-log query; the repository layer
    combines multiple scopes with ``OR`` to realize the ``AuditLogScope``
    union semantics.

    ``existence_checks`` is empty by ``SearchableActionTarget`` convention —
    RBAC validation already gates entity reachability.
    """

    entity_type: RBACElementType
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
class TriggeredByAuditLogSearchScope(SearchScope):
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
