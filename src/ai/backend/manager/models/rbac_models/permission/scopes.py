"""Operation scopes for permissions."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.errors.permission import RoleNotFound
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope
from ai.backend.manager.models.user.row import UserRow

__all__ = (
    "PermissionOperationScope",
    "ObjectPermissionOperationScope",
    "AssignedUserPermissionOperationScope",
)


@dataclass(frozen=True)
class PermissionOperationScope(OperationScope):
    """Scope for searching scoped permissions by role."""

    role_id: uuid.UUID

    @override
    def to_condition(self) -> QueryCondition:
        role_id = self.role_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionRow.role_id == role_id

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return [
            ExistenceCheck(
                column=RoleRow.id,
                value=self.role_id,
                error=RoleNotFound(),
            ),
        ]


@dataclass(frozen=True)
class ObjectPermissionOperationScope(OperationScope):
    """Scope for searching object permissions by role."""

    role_id: uuid.UUID

    @override
    def to_condition(self) -> QueryCondition:
        role_id = self.role_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ObjectPermissionRow.role_id == role_id

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return [
            ExistenceCheck(
                column=RoleRow.id,
                value=self.role_id,
                error=RoleNotFound(),
            ),
        ]


@dataclass(frozen=True)
class AssignedUserPermissionOperationScope(OperationScope):
    """The permissions one user holds: those carried by the active roles assigned to them.

    Matched on the roles rather than on the user, since a permission row names only the
    role granting it. Revoked and deleted roles carry nothing, so only ACTIVE ones count.
    """

    user_id: UserID

    @override
    def to_condition(self) -> QueryCondition:
        user_id = self.user_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subq = (
                sa.select(sa.literal(1))
                .select_from(sa.join(UserRoleRow, RoleRow, UserRoleRow.role_id == RoleRow.id))
                .where(
                    UserRoleRow.role_id == PermissionRow.role_id,
                    UserRoleRow.user_id == user_id,
                    RoleRow.status == RoleStatus.ACTIVE,
                )
                .correlate(PermissionRow)
            )
            return sa.exists(subq)

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return [
            ExistenceCheck(
                column=UserRow.uuid,
                value=self.user_id,
                error=UserNotFound(),
            ),
        ]
