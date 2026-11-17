"""What a role preset search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

import sqlalchemy as sa

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.role_preset import RolePresetEntityType
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.models.entity_label.query_spec import (
    EntityLabelCorrelation,
    EntityLabelQuerySpec,
)
from ai.backend.manager.models.global_entity.row import GlobalEntityRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.role_permission_preset.query_spec import (
    RolePermissionPresetQuerySpec,
)
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
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
from ai.backend.manager.models.specs.search.correlation import ToManyCorrelation
from ai.backend.manager.models.specs.search.field import (
    NestedQueryColumn,
    QueryColumn,
)
from ai.backend.manager.models.specs.search.usage import UsedByConditions

__all__ = ("RolePresetQuerySpec",)

_SCOPE_TYPE_OR_GLOBAL_ENTITY_NAME = sa.type_coerce(
    sa.func.coalesce(
        sa.select(GlobalEntityRow.name)
        .where(
            RolePresetRow.scope_type == GlobalEntityType(),
            GlobalEntityRow.id == RolePresetRow.scope_id,
        )
        .scalar_subquery(),
        RolePresetRow.scope_type,
    ),
    sa.String(),
)


class _RolePresetOwnColumns(RowDataConverter[RolePresetRow, RolePresetData]):
    """The preset's own columns.

    ``role_name_template`` is ``sa.Text`` with no index serving a partial match, so it
    carries equality and membership only. ``scope_type`` filters and orders on the value
    the API shows: a ``global`` preset's global entity name.
    """

    id = QueryColumn(
        RolePresetRow.id, UUIDConditions(RolePresetRow.id), ColumnOrder(RolePresetRow.id)
    )
    name = QueryColumn(
        RolePresetRow.name,
        StringConditions(RolePresetRow.name),
        ColumnOrder(RolePresetRow.name),
    )
    role_name_template = QueryColumn(
        RolePresetRow.role_name_template,
        StringEqualityConditions(RolePresetRow.role_name_template),
        ColumnOrder(RolePresetRow.role_name_template),
    )
    scope_type = QueryColumn(
        RolePresetRow.scope_type,
        StringConditions(_SCOPE_TYPE_OR_GLOBAL_ENTITY_NAME),
        ColumnOrder(_SCOPE_TYPE_OR_GLOBAL_ENTITY_NAME),
    )
    scope_id = QueryColumn(
        RolePresetRow.scope_id,
        UUIDConditions(RolePresetRow.scope_id),
        ColumnOrder(RolePresetRow.scope_id),
    )
    auto_assign = QueryColumn(
        RolePresetRow.auto_assign,
        BoolConditions(RolePresetRow.auto_assign),
        ColumnOrder(RolePresetRow.auto_assign),
    )
    auto_assign_to_owner = QueryColumn(
        RolePresetRow.auto_assign_to_owner,
        BoolConditions(RolePresetRow.auto_assign_to_owner),
        ColumnOrder(RolePresetRow.auto_assign_to_owner),
    )
    deleted_at = QueryColumn(
        RolePresetRow.deleted_at,
        DateTimeConditions(RolePresetRow.deleted_at),
        ColumnOrder(RolePresetRow.deleted_at),
    )
    created_at = QueryColumn(
        RolePresetRow.created_at,
        DateTimeConditions(RolePresetRow.created_at),
        ColumnOrder(RolePresetRow.created_at),
    )
    updated_at = QueryColumn(
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
            scope_id=self.scope_id.read(row),
            auto_assign=self.auto_assign.read(row),
            auto_assign_to_owner=self.auto_assign_to_owner.read(row),
            deleted_at=self.deleted_at.read(row),
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
        )


class _RolePresetNestedColumns:
    """The permission entries and labels the preset owns, read under the preset's own
    permission.

    A permission entry is the preset's field row, so one permission answers for the
    pair. Narrowing a preset search by permission does not replace the permission
    search, which lists the rows themselves.
    """

    permissions = NestedQueryColumn(
        RolePermissionPresetQuerySpec.own,
        ToManyCorrelation(
            RolePermissionPresetRow,
            RolePresetRow,
            RolePermissionPresetRow.role_preset_id == RolePresetRow.id,
        ),
    )
    labels = NestedQueryColumn(
        EntityLabelQuerySpec.own,
        EntityLabelCorrelation(RolePresetRow, RolePresetEntityType(), RolePresetRow.id),
    )


class _RolePresetUsage:
    """Uses between a preset and other entities."""

    roles = UsedByConditions[RoleID](
        ToManyCorrelation(RoleRow, RolePresetRow, RoleRow.role_preset_id == RolePresetRow.id),
        RoleRow.id,
    )
    """Presets a role was instantiated from."""


class _RolePresetLinkedEntities:
    """How a preset connects to other entities; the other entity's permission governs."""

    usage = _RolePresetUsage


class RolePresetQuerySpec:
    own = _RolePresetOwnColumns()
    nested = _RolePresetNestedColumns
    linked = _RolePresetLinkedEntities
