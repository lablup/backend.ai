"""What a role search can filter and order by, and how a role row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.manager.data.permission.role import RoleData, RoleDetailData
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import RoleSource
from ai.backend.manager.models.entity_label.query_spec import (
    EntityLabelCorrelation,
    EntityLabelQuerySpec,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.query_spec import (
    PermissionQuerySpec,
)
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
from ai.backend.manager.models.specs.search.field import (
    NestedQueryColumn,
    QueryColumn,
)
from ai.backend.manager.models.specs.search.usage import UsesConditions

__all__ = ("RoleQuerySpec",)


class _RoleOwnColumns(RowDataConverter[RoleRow, RoleData]):
    """The role's own columns.

    ``description`` is ``sa.Text`` with no index serving a partial match, so it carries
    equality and membership only.
    """

    id = QueryColumn(RoleRow.id, UUIDConditions(RoleRow.id), ColumnOrder(RoleRow.id))
    name = QueryColumn(RoleRow.name, StringConditions(RoleRow.name), ColumnOrder(RoleRow.name))
    description = QueryColumn(
        RoleRow.description,
        StringEqualityConditions(RoleRow.description),
        ColumnOrder(RoleRow.description),
    )
    source = QueryColumn(
        RoleRow.source, EnumConditions(RoleRow.source, RoleSource), ColumnOrder(RoleRow.source)
    )
    status = QueryColumn(
        RoleRow.status, EnumConditions(RoleRow.status, RoleStatus), ColumnOrder(RoleRow.status)
    )
    auto_assign = QueryColumn(
        RoleRow.auto_assign,
        BoolConditions(RoleRow.auto_assign),
        ColumnOrder(RoleRow.auto_assign),
    )
    scope_type = QueryColumn(
        RoleRow.scope_type,
        StringConditions(RoleRow.scope_type),
        ColumnOrder(RoleRow.scope_type),
    )
    scope_id = QueryColumn(
        RoleRow.scope_id, UUIDConditions(RoleRow.scope_id), ColumnOrder(RoleRow.scope_id)
    )
    role_preset_id = QueryColumn(
        RoleRow.role_preset_id,
        UUIDConditions(RoleRow.role_preset_id),
        ColumnOrder(RoleRow.role_preset_id),
    )
    created_at = QueryColumn(
        RoleRow.created_at,
        DateTimeConditions(RoleRow.created_at),
        ColumnOrder(RoleRow.created_at),
    )
    updated_at = QueryColumn(
        RoleRow.updated_at,
        DateTimeConditions(RoleRow.updated_at),
        ColumnOrder(RoleRow.updated_at),
    )
    deleted_at = QueryColumn(
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


class _RoleNestedColumns:
    """The permission entries and labels the role owns, read under the role's own permission.

    A permission entry is the role's field row, so one permission answers for the pair.
    """

    permissions = NestedQueryColumn(
        PermissionQuerySpec.own,
        ToManyCorrelation(PermissionRow, RoleRow, PermissionRow.role_id == RoleRow.id),
    )
    labels = NestedQueryColumn(
        EntityLabelQuerySpec.own,
        EntityLabelCorrelation(RoleRow, RoleEntityType(), RoleRow.id),
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


class RoleQuerySpec:
    own = _RoleOwnColumns()
    nested = _RoleNestedColumns
    linked = _RoleLinkedEntities
