from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.permission.role import AssignedUserData
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.rbac_models.user_role.searchable_fields import (
    RoleAssignmentSearchableFields,
)
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import FieldUpserter

__all__ = ("UserRoleUpserter",)


@dataclass
class UserRoleUpserter(FieldUpserter[RoleID, UserRoleRow, AssignedUserData]):
    """Grant a role to a user as the system does, keeping a grant the user already holds.

    Conflict key: the user and the role.
    """

    user_id: UserID

    @override
    def row_class(self) -> type[UserRoleRow]:
        return UserRoleRow

    @override
    def index_elements(self) -> list[str]:
        return ["user_id", "role_id"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self, owner_id: RoleID) -> dict[str, Any]:
        return {"user_id": self.user_id, "role_id": owner_id, "granted_by": None}

    @override
    def build_update_values(self) -> dict[str, Any]:
        """Nothing: who granted the role and when stay as they are."""
        return {}

    @override
    def to_data(self, row: UserRoleRow) -> AssignedUserData:
        return RoleAssignmentSearchableFields.own.to_data(row)
