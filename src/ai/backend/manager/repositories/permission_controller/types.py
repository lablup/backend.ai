from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import sqlalchemy as sa

from ai.backend.common.data.permission.types import EntityType, ScopeType
from ai.backend.manager.errors.permission import RoleNotFound
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
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


@dataclass(frozen=True)
class RoleSearchScope(SearchScope):
    """Scope for searching roles visible to a specific user via RBAC.

    A role is visible to a user if:
    - The user has a direct role assignment via user_roles, OR
    - The user is associated with the role scope via association_scopes_entities
      (entity_type=USER, scope_type=ROLE)
    """

    user_id: uuid.UUID

    def to_condition(self) -> QueryCondition:
        user_id = self.user_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            user_id_str = str(user_id)

            # Roles directly assigned via user_roles
            direct_assignment = sa.select(UserRoleRow.role_id).where(
                UserRoleRow.user_id == user_id,
            )

            # Roles visible via association_scopes_entities scope chain
            # Cast role ID to text to match scope_id (String column)
            scope_association = sa.select(
                sa.cast(AssociationScopesEntitiesRow.scope_id, sa.Uuid),
            ).where(
                sa.and_(
                    AssociationScopesEntitiesRow.entity_type == EntityType.USER,
                    AssociationScopesEntitiesRow.entity_id == user_id_str,
                    AssociationScopesEntitiesRow.scope_type == ScopeType.ROLE,
                ),
            )

            return RoleRow.id.in_(direct_assignment.union(scope_association))

        return inner

    @property
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return []
