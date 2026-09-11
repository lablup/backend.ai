"""Read specs keyed by the assignment rows' own ids."""

from __future__ import annotations

from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.manager.data.permission.role import AssignedUserData
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.specs.querier import BulkFieldQuerier


class BulkUserRoleQuerier(BulkFieldQuerier[UserRoleRow, AssignedUserData]):
    """The role assignments the caller named."""

    @override
    def row_class(self) -> type[UserRoleRow]:
        return UserRoleRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return UserRoleRow.id

    @override
    def to_data(self, row: UserRoleRow) -> AssignedUserData:
        return row.to_assigned_user_data()
