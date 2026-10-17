"""Operation scopes for audit logs."""

from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.models.audit_log.row import AuditLogRow
from ai.backend.manager.models.audit_log.scope_row import AuditLogScopeRow
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.scopes import ExistenceCheck, ScopeTarget

__all__ = (
    "AuditLogTarget",
    "EntityAuditLogTarget",
    "TriggeredByAuditLogTarget",
)


class AuditLogTarget(ScopeTarget, ABC):
    """One entity a scoped audit-log read runs within.

    Which entity authorizes the read and which rows it selects differ here: an actor's
    records are answered for at that user but matched on a different column than an
    entity's own.
    """


@dataclass(frozen=True)
class EntityAuditLogTarget(AuditLogTarget):
    """The records of one entity's history: the runs that touched it, and the runs that
    named it as a scope they ran in on ``audit_log_scopes``.

    ``existence_checks`` is empty -- RBAC validation already gates entity reachability.
    """

    owner: EntityIdentifier

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.owner

    @override
    def to_condition(self) -> QueryCondition:
        owner = self.owner

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.or_(
                sa.and_(
                    AuditLogRow.entity_type == owner.entity_type(),
                    AuditLogRow.entity_id == str(owner),
                ),
                sa.exists().where(
                    sa.and_(
                        AuditLogScopeRow.audit_log_id == AuditLogRow.id,
                        AuditLogScopeRow.scope_type == owner.entity_type(),
                        AuditLogScopeRow.scope_id == str(owner),
                    )
                ),
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()


@dataclass(frozen=True)
class TriggeredByAuditLogTarget(AuditLogTarget):
    """The records one user triggered, whoever they were about."""

    user_id: UserID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.user_id

    @override
    def to_condition(self) -> QueryCondition:
        triggered_by = str(self.user_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AuditLogRow.triggered_by == triggered_by

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
