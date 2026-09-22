"""Lookup specs for role assignment rows."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.specs.lookup import BulkDataLookup

__all__ = (
    "RoleAssignmentRolesLookup",
    "RoleAssignmentUsersLookup",
)


class RoleAssignmentRolesLookup(BulkDataLookup[UUID, RoleID]):
    """Resolves several assignment row ids into the roles those rows join to."""

    @override
    def build_query(self, keys: Sequence[UUID]) -> sa.sql.Select[Any]:
        return sa.select(UserRoleRow.id, UserRoleRow.role_id).where(UserRoleRow.id.in_(keys))

    @override
    def to_entity_id(self, value: UUID) -> RoleID:
        return RoleID(value)


class RoleAssignmentUsersLookup(BulkDataLookup[UUID, UserID]):
    """Resolves several assignment row ids into the users those rows join to."""

    @override
    def build_query(self, keys: Sequence[UUID]) -> sa.sql.Select[Any]:
        return sa.select(UserRoleRow.id, UserRoleRow.user_id).where(UserRoleRow.id.in_(keys))

    @override
    def to_entity_id(self, value: UUID) -> UserID:
        return UserID(value)
