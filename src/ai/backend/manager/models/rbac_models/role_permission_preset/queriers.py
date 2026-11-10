"""BulkFieldQuerier implementation for the role_permission_presets table."""

from __future__ import annotations

from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.manager.data.role_preset.types import RolePermissionPresetData
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_permission_preset.searchable_fields import (
    RolePermissionPresetSearchableFields,
)
from ai.backend.manager.models.specs.querier import BulkFieldQuerier


class BulkRolePermissionPresetQuerier(
    BulkFieldQuerier[RolePermissionPresetRow, RolePermissionPresetData]
):
    """The preset permission entries the caller named."""

    @override
    def row_class(self) -> type[RolePermissionPresetRow]:
        return RolePermissionPresetRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return RolePermissionPresetRow.id

    @override
    def to_data(self, row: RolePermissionPresetRow) -> RolePermissionPresetData:
        return RolePermissionPresetSearchableFields.own.to_data(row)
