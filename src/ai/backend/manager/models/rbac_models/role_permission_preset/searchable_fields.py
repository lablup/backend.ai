"""What a preset permission search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.data.role_preset.types import RolePermissionPresetData
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField

__all__ = ("RolePermissionPresetSearchableFields",)


class _RolePermissionPresetOwnFields(
    RowDataConverter[RolePermissionPresetRow, RolePermissionPresetData]
):
    """The preset permission entry's own columns."""

    id = SearchableField(
        RolePermissionPresetRow.id,
        UUIDConditions(RolePermissionPresetRow.id),
        ColumnOrder(RolePermissionPresetRow.id),
    )
    role_preset_id = SearchableField(
        RolePermissionPresetRow.role_preset_id,
        UUIDConditions(RolePermissionPresetRow.role_preset_id),
        ColumnOrder(RolePermissionPresetRow.role_preset_id),
    )
    entity_type = SearchableField(
        RolePermissionPresetRow.entity_type,
        StringConditions(RolePermissionPresetRow.entity_type),
        ColumnOrder(RolePermissionPresetRow.entity_type),
    )
    permission = SearchableField(
        RolePermissionPresetRow.permission,
        EnumConditions(RolePermissionPresetRow.permission, Permission),
        ColumnOrder(RolePermissionPresetRow.permission),
    )
    created_at = SearchableField(
        RolePermissionPresetRow.created_at,
        DateTimeConditions(RolePermissionPresetRow.created_at),
        ColumnOrder(RolePermissionPresetRow.created_at),
    )

    @override
    def to_data(self, row: RolePermissionPresetRow) -> RolePermissionPresetData:
        return RolePermissionPresetData(
            id=self.id.read(row),
            role_preset_id=self.role_preset_id.read(row),
            entity_type=self.entity_type.read(row),
            permission=self.permission.read(row),
            created_at=self.created_at.read(row),
        )


class RolePermissionPresetSearchableFields:
    own = _RolePermissionPresetOwnFields()
