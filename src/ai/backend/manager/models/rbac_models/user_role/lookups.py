"""Read specs for role assignments."""

from __future__ import annotations

from collections.abc import Sequence
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.user_role import UserRoleAssignmentID
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.specs.lookup import FieldOwnerLookup


class UserRoleOwnerLookup(FieldOwnerLookup[UserRoleAssignmentID, UserID]):
    """The user a role assignment belongs to."""

    @override
    def build_query(
        self, field_ids: Sequence[UserRoleAssignmentID]
    ) -> sa.sql.Select[tuple[UserRoleAssignmentID, UserID]]:
        return sa.select(UserRoleRow.id, UserRoleRow.user_id).where(UserRoleRow.id.in_(field_ids))

    @override
    def to_entity_id(self, value: UUID) -> UserID:
        return UserID(value)
