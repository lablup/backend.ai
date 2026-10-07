from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.role_preset.types import RolePermissionPresetData
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_permission_preset.searchable_fields import (
    RolePermissionPresetSearchableFields,
)
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import FieldUpserter

__all__ = ("RolePermissionPresetUpserter",)


@dataclass
class RolePermissionPresetUpserter(
    FieldUpserter[RolePresetID, RolePermissionPresetRow, RolePermissionPresetData]
):
    """Grant one bit on one entity type to a preset, keeping the row it already has.

    Conflict key: the preset, the entity type and the bit.
    """

    entity_type: EntityType
    permission: Permission

    @override
    def row_class(self) -> type[RolePermissionPresetRow]:
        return RolePermissionPresetRow

    @override
    def index_elements(self) -> list[str]:
        return ["role_preset_id", "entity_type", "permission"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self, owner_id: RolePresetID) -> dict[str, Any]:
        return {
            "role_preset_id": owner_id,
            "entity_type": self.entity_type,
            "permission": self.permission,
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        """The row holds nothing beyond its key; rewriting the bit returns it unchanged."""
        return {"permission": self.permission}

    @override
    def to_data(self, row: RolePermissionPresetRow) -> RolePermissionPresetData:
        return RolePermissionPresetSearchableFields.own.to_data(row)
