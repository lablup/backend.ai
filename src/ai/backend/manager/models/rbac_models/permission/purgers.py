from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.permission import PermissionID
from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.searchable_fields import (
    PermissionSearchableFields,
)
from ai.backend.manager.models.specs.purger import FieldBatchPurger, FieldPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class RolePermissionPurger(FieldPurger[PermissionRow, PermissionData]):
    """Purger for one permission entry, authorized through its role. The paths the
    entry is scoped to follow by FK cascade."""

    permission_id: PermissionID

    @override
    def row_class(self) -> type[PermissionRow]:
        return PermissionRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return PermissionRow.id

    @override
    def target_id_value(self) -> PermissionID:
        return self.permission_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: PermissionRow) -> PermissionData:
        return PermissionSearchableFields.own.to_data(row)


@dataclass
class RolePermissionUngrantedPurger(FieldBatchPurger[RoleID, PermissionRow, PermissionData]):
    """Drops a role's permission rows on the named entity types that the given masks
    leave out. An entity type absent from ``grants`` keeps its rows; one mapped to an
    empty mask loses all of them."""

    grants: Mapping[EntityType, Permission]

    @override
    def build_subquery(self, owner_id: RoleID) -> sa.sql.Select[Any]:
        row = PermissionRow
        return sa.select(row).where(
            row.role_id == owner_id,
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
    def to_data(self, row: PermissionRow) -> PermissionData:
        return PermissionSearchableFields.own.to_data(row)
