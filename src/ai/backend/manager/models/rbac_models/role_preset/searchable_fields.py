"""What a role preset search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.string import (
    StringConditions,
    StringEqualityConditions,
)
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField

__all__ = ("RolePresetSearchableFields",)


class _RolePresetOwnFields(RowDataConverter[RolePresetRow, RolePresetData]):
    """The preset's own columns.

    ``role_name_template`` is ``sa.Text`` with no index serving a partial match, so it
    carries equality and membership only.
    """

    id = SearchableField(
        RolePresetRow.id, UUIDConditions(RolePresetRow.id), ColumnOrder(RolePresetRow.id)
    )
    name = SearchableField(
        RolePresetRow.name,
        StringConditions(RolePresetRow.name),
        ColumnOrder(RolePresetRow.name),
    )
    role_name_template = SearchableField(
        RolePresetRow.role_name_template,
        StringEqualityConditions(RolePresetRow.role_name_template),
        ColumnOrder(RolePresetRow.role_name_template),
    )
    scope_type = SearchableField(
        RolePresetRow.scope_type,
        StringConditions(RolePresetRow.scope_type),
        ColumnOrder(RolePresetRow.scope_type),
    )
    scope_id = SearchableField(
        RolePresetRow.scope_id,
        UUIDConditions(RolePresetRow.scope_id),
        ColumnOrder(RolePresetRow.scope_id),
    )
    auto_assign = SearchableField(
        RolePresetRow.auto_assign,
        BoolConditions(RolePresetRow.auto_assign),
        ColumnOrder(RolePresetRow.auto_assign),
    )
    deleted = SearchableField(
        RolePresetRow.deleted,
        BoolConditions(RolePresetRow.deleted),
        ColumnOrder(RolePresetRow.deleted),
    )
    created_at = SearchableField(
        RolePresetRow.created_at,
        DateTimeConditions(RolePresetRow.created_at),
        ColumnOrder(RolePresetRow.created_at),
    )
    updated_at = SearchableField(
        RolePresetRow.updated_at,
        DateTimeConditions(RolePresetRow.updated_at),
        ColumnOrder(RolePresetRow.updated_at),
    )

    @override
    def to_data(self, row: RolePresetRow) -> RolePresetData:
        return RolePresetData(
            id=self.id.read(row),
            name=self.name.read(row),
            role_name_template=self.role_name_template.read(row),
            scope_type=self.scope_type.read(row),
            auto_assign=self.auto_assign.read(row),
            deleted=self.deleted.read(row),
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
        )


class RolePresetSearchableFields:
    own = _RolePresetOwnFields()
