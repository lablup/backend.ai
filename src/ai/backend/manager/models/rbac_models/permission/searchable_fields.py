"""What a permission search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField

__all__ = ("PermissionSearchableFields",)


class _PermissionOwnFields(RowDataConverter[PermissionRow, PermissionData]):
    """The permission entry's own columns."""

    id = SearchableField(
        PermissionRow.id, UUIDConditions(PermissionRow.id), ColumnOrder(PermissionRow.id)
    )
    role_id = SearchableField(
        PermissionRow.role_id,
        UUIDConditions(PermissionRow.role_id),
        ColumnOrder(PermissionRow.role_id),
    )
    entity_type = SearchableField(
        PermissionRow.entity_type,
        StringConditions(PermissionRow.entity_type),
        ColumnOrder(PermissionRow.entity_type),
    )
    permission = SearchableField(
        PermissionRow.permission,
        EnumConditions(PermissionRow.permission, Permission),
        ColumnOrder(PermissionRow.permission),
    )
    all_fields = SearchableField(
        PermissionRow.all_fields,
        BoolConditions(PermissionRow.all_fields),
        ColumnOrder(PermissionRow.all_fields),
    )
    created_at = SearchableField(
        PermissionRow.created_at,
        DateTimeConditions(PermissionRow.created_at),
        ColumnOrder(PermissionRow.created_at),
    )

    @override
    def to_data(self, row: PermissionRow) -> PermissionData:
        return PermissionData(
            id=self.id.read(row),
            role_id=self.role_id.read(row),
            entity_type=self.entity_type.read(row),
            permission=self.permission.read(row),
            created_at=self.created_at.read(row),
        )


class PermissionSearchableFields:
    own = _PermissionOwnFields()
