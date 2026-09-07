"""Operation scopes for roles."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.role import ROLE_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope
from ai.backend.manager.models.virtual_entity.conditions import OwningScopeConditions
from ai.backend.manager.models.virtual_entity.queries import owning_scope_exists


@dataclass(frozen=True)
class ScopedRoleOperationScope(OperationScope):
    """The roles a given scope (project, domain, ...) owns."""

    scope: EntityIdentifier

    @override
    def to_condition(self) -> QueryCondition:
        scope = self.scope

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return owning_scope_exists(
                ROLE_ENTITY_TYPE,
                RoleRow.id,
                (
                    OwningScopeConditions.by_scope_type_equals(scope.entity_type()),
                    OwningScopeConditions.by_scope_id(scope),
                ),
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return []
