"""Searcher implementations for role assignment rows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.permission.role import AssignedUserData
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.specs.searcher import Searcher
from ai.backend.manager.models.user.row import UserRow

__all__ = ("RoleAssignmentSearcher",)


@dataclass
class RoleAssignmentSearcher(Searcher[UserRoleRow, AssignedUserData]):
    """Assignment rows, joined to their users for the username and email conditions."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(UserRoleRow).join(UserRow, UserRoleRow.user_id == UserRow.uuid)

    @override
    def to_data(self, row: UserRoleRow) -> AssignedUserData:
        return row.to_assigned_user_data()
