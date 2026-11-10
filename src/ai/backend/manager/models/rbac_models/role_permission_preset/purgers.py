from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.role_permission_preset import RolePermissionPresetID
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
from ai.backend.manager.models.specs.purger import FieldBatchPurger, FieldPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class RolePermissionPresetPurger(FieldPurger[RolePermissionPresetRow, RolePermissionPresetData]):
    """Purger for one permission entry, authorized through its preset."""

    permission_preset_id: RolePermissionPresetID

    @override
    def row_class(self) -> type[RolePermissionPresetRow]:
        return RolePermissionPresetRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return RolePermissionPresetRow.id

    @override
    def target_id_value(self) -> RolePermissionPresetID:
        return self.permission_preset_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: RolePermissionPresetRow) -> RolePermissionPresetData:
        return RolePermissionPresetSearchableFields.own.to_data(row)


@dataclass
class RolePermissionPresetUngrantedPurger(
    FieldBatchPurger[RolePresetID, RolePermissionPresetRow, RolePermissionPresetData]
):
    """Drops a preset's permission rows on the named entity types that the given masks
    leave out. An entity type absent from ``grants`` keeps its rows; one mapped to an
    empty mask loses all of them."""

    grants: Mapping[EntityType, Permission]

    @override
    def build_subquery(self, owner_id: RolePresetID) -> sa.sql.Select[Any]:
        row = RolePermissionPresetRow
        return sa.select(row).where(
            row.role_preset_id == owner_id,
            sa.or_(
                *(
                    sa.and_(row.entity_type == entity_type, row.permission.not_in(list(mask)))
                    for entity_type, mask in self.grants.items()
                )
            ),
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: RolePermissionPresetRow) -> RolePermissionPresetData:
        return RolePermissionPresetSearchableFields.own.to_data(row)
