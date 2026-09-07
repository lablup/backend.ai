"""Read specs for role permissions."""

from __future__ import annotations

from collections.abc import Sequence
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.permission import PermissionID
from ai.backend.common.data.entity.role import RoleID
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.specs.lookup import FieldOwnerLookup


class RolePermissionOwnerLookup(FieldOwnerLookup[PermissionID, RoleID]):
    """The role a permission entry belongs to."""

    @override
    def build_query(
        self, field_ids: Sequence[PermissionID]
    ) -> sa.sql.Select[tuple[PermissionID, RoleID]]:
        return sa.select(PermissionRow.id, PermissionRow.role_id).where(
            PermissionRow.id.in_(field_ids)
        )

    @override
    def to_entity_id(self, value: UUID) -> RoleID:
        return RoleID(value)
