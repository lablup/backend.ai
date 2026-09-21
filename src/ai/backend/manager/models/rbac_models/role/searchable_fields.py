"""What a role search can filter and order by, and how a role row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.manager.data.permission.role import RoleData, RoleDetailData
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import RoleSource
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.string import (
    StringConditions,
    StringEqualityConditions,
)
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.correlation import ToManyCorrelation
from ai.backend.manager.models.specs.search.field import SearchableField
from ai.backend.manager.models.specs.search.usage import UsesConditions

__all__ = ("RoleSearchableFields",)


class _RoleOwnFields(RowDataConverter[RoleRow, RoleData]):
    """The role's own columns.

    ``description`` is ``sa.Text`` with no index serving a partial match, so it carries
    equality and membership only.
    """

    id = SearchableField(RoleRow.id, UUIDConditions(RoleRow.id), ColumnOrder(RoleRow.id))
    name = SearchableField(RoleRow.name, StringConditions(RoleRow.name), ColumnOrder(RoleRow.name))
    description = SearchableField(
        RoleRow.description,
        StringEqualityConditions(RoleRow.description),
        ColumnOrder(RoleRow.description),
    )
    source = SearchableField(
        RoleRow.source, EnumConditions(RoleRow.source, RoleSource), ColumnOrder(RoleRow.source)
    )
    status = SearchableField(
        RoleRow.status, EnumConditions(RoleRow.status, RoleStatus), ColumnOrder(RoleRow.status)
    )
    auto_assign = SearchableField(
        RoleRow.auto_assign,
        BoolConditions(RoleRow.auto_assign),
        ColumnOrder(RoleRow.auto_assign),
    )
    scope_type = SearchableField(
        RoleRow.scope_type,
        StringConditions(RoleRow.scope_type),
        ColumnOrder(RoleRow.scope_type),
    )
    scope_id = SearchableField(
        RoleRow.scope_id, UUIDConditions(RoleRow.scope_id), ColumnOrder(RoleRow.scope_id)
    )
    role_preset_id = SearchableField(
        RoleRow.role_preset_id,
        UUIDConditions(RoleRow.role_preset_id),
        ColumnOrder(RoleRow.role_preset_id),
    )
    created_at = SearchableField(
        RoleRow.created_at,
        DateTimeConditions(RoleRow.created_at),
        ColumnOrder(RoleRow.created_at),
    )
    updated_at = SearchableField(
        RoleRow.updated_at,
        DateTimeConditions(RoleRow.updated_at),
        ColumnOrder(RoleRow.updated_at),
    )
    deleted_at = SearchableField(
        RoleRow.deleted_at,
        DateTimeConditions(RoleRow.deleted_at),
        ColumnOrder(RoleRow.deleted_at),
    )

    @override
    def to_data(self, row: RoleRow) -> RoleData:
        return RoleData(
            id=self.id.read(row),
            name=self.name.read(row),
            source=self.source.read(row),
            status=self.status.read(row),
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
            deleted_at=self.deleted_at.read(row),
            scope_type=self.scope_type.read(row),
            scope_id=self.scope_id.read(row),
            auto_assign=self.auto_assign.read(row),
            description=self.description.read(row),
            role_preset_id=self.role_preset_id.read(row),
        )

    def to_detail_data(self, row: RoleRow) -> RoleDetailData:
        """The same values under the shape the role detail read answers with."""
        return RoleDetailData(
            id=self.id.read(row),
            name=self.name.read(row),
            source=self.source.read(row),
            status=self.status.read(row),
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
            deleted_at=self.deleted_at.read(row),
            scope_type=self.scope_type.read(row),
            scope_id=self.scope_id.read(row),
            auto_assign=self.auto_assign.read(row),
            description=self.description.read(row),
            role_preset_id=self.role_preset_id.read(row),
        )


class _RoleUsage:
    """Uses between a role and other entities."""

    role_presets = UsesConditions[RolePresetID](
        ToManyCorrelation(RolePresetRow, RoleRow, RolePresetRow.id == RoleRow.role_preset_id),
        RolePresetRow.id,
    )
    """Roles instantiated from the preset."""


class _RoleLinkedEntities:
    """How a role connects to other entities; the other entity's permission governs."""

    usage = _RoleUsage


class RoleSearchableFields:
    own = _RoleOwnFields()
    linked = _RoleLinkedEntities
