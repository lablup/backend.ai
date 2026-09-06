"""Operation scopes for roles."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.permission.types import EntityType, RBACElementType
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope


@dataclass(frozen=True)
class ScopedRoleOperationScope(OperationScope):
    """Scope for searching roles registered in a given scope (project, domain, etc.)."""

    element_type: RBACElementType
    scope_id: str

    @override
    def to_condition(self) -> QueryCondition:
        element_type = self.element_type
        scope_id = self.scope_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subq = sa.select(AssociationScopesEntitiesRow.entity_id).where(
                AssociationScopesEntitiesRow.scope_type == element_type.to_scope_type(),
                AssociationScopesEntitiesRow.scope_id == scope_id,
                AssociationScopesEntitiesRow.entity_type == EntityType.ROLE,
            )
            return sa.cast(RoleRow.id, sa.String).in_(subq)

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return []
