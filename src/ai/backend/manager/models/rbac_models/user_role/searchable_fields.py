"""What a role assignment search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.manager.data.permission.role import AssignedUserData, UserRoleAssignmentData
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField

__all__ = ("RoleAssignmentSearchableFields",)


class _RoleAssignmentOwnFields(RowDataConverter[UserRoleRow, AssignedUserData]):
    """The assignment row's own columns."""

    id = SearchableField(
        UserRoleRow.id, UUIDConditions(UserRoleRow.id), ColumnOrder(UserRoleRow.id)
    )
    user_id = SearchableField(
        UserRoleRow.user_id,
        UUIDConditions(UserRoleRow.user_id),
        ColumnOrder(UserRoleRow.user_id),
    )
    role_id = SearchableField(
        UserRoleRow.role_id,
        UUIDConditions(UserRoleRow.role_id),
        ColumnOrder(UserRoleRow.role_id),
    )
    granted_by = SearchableField(
        UserRoleRow.granted_by,
        UUIDConditions(UserRoleRow.granted_by),
        ColumnOrder(UserRoleRow.granted_by),
    )
    granted_at = SearchableField(
        UserRoleRow.granted_at,
        DateTimeConditions(UserRoleRow.granted_at),
        ColumnOrder(UserRoleRow.granted_at),
    )

    @override
    def to_data(self, row: UserRoleRow) -> AssignedUserData:
        return AssignedUserData(
            id=self.id.read(row),
            user_id=self.user_id.read(row),
            role_id=self.role_id.read(row),
            granted_by=self.granted_by.read(row),
            granted_at=self.granted_at.read(row),
        )

    def to_assignment_data(self, row: UserRoleRow) -> UserRoleAssignmentData:
        """The same row under the shape a write answers with, which omits the moment."""
        return UserRoleAssignmentData(
            id=self.id.read(row),
            user_id=self.user_id.read(row),
            role_id=self.role_id.read(row),
            granted_by=self.granted_by.read(row),
        )


class RoleAssignmentSearchableFields:
    own = _RoleAssignmentOwnFields()
