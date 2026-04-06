from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import sqlalchemy as sa

from ai.backend.common.data.permission.types import EntityType, RBACElementType
from ai.backend.manager.errors.permission import RoleNotFound
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base import BatchQuerierResult
from ai.backend.manager.repositories.base.types import ExistenceCheck, QueryCondition, SearchScope


class RoleBatchQuerierResult(BatchQuerierResult[RoleRow]):
    pass


class AssignedUserBatchQuerierResult(BatchQuerierResult[UserRow]):
    pass


@dataclass(frozen=True)
class PermissionSearchScope(SearchScope):
    """Scope for searching scoped permissions by role."""

    role_id: uuid.UUID

    def to_condition(self) -> QueryCondition:
        role_id = self.role_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionRow.role_id == role_id

        return inner

    @property
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return [
            ExistenceCheck(
                column=RoleRow.id,
                value=self.role_id,
                error=RoleNotFound(),
            ),
        ]


@dataclass(frozen=True)
class ScopedRoleSearchScope(SearchScope):
    """Scope for searching roles registered in a given scope (project, domain, etc.)."""

    element_type: RBACElementType
    scope_id: str

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
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return []


@dataclass(frozen=True)
class ObjectPermissionSearchScope(SearchScope):
    """Scope for searching object permissions by role."""

    role_id: uuid.UUID

    def to_condition(self) -> QueryCondition:
        role_id = self.role_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ObjectPermissionRow.role_id == role_id

        return inner

    @property
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return [
            ExistenceCheck(
                column=RoleRow.id,
                value=self.role_id,
                error=RoleNotFound(),
            ),
        ]
