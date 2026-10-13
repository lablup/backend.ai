from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.searchable_fields import (
    PermissionSearchableFields,
)
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import FieldUpserter

__all__ = ("RolePermissionUpserter",)


@dataclass
class RolePermissionUpserter(FieldUpserter[RoleID, PermissionRow, PermissionData]):
    """Grant one bit on one entity type to a role, keeping the row it already has.

    Conflict key: the role, the entity type and the bit. A new row covers every field.
    """

    entity_type: EntityType
    permission: Permission

    @override
    def row_class(self) -> type[PermissionRow]:
        return PermissionRow

    @override
    def index_elements(self) -> list[str]:
        return ["role_id", "entity_type", "permission"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self, owner_id: RoleID) -> dict[str, Any]:
        return {
            "role_id": owner_id,
            "entity_type": self.entity_type,
            "permission": self.permission,
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        """The row holds nothing beyond its key; rewriting the bit returns it unchanged."""
        return {"permission": self.permission}

    @override
    def to_data(self, row: PermissionRow) -> PermissionData:
        return PermissionSearchableFields.own.to_data(row)
