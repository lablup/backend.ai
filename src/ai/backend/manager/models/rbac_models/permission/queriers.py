"""Read specs keyed by the permission rows' own ids."""

from __future__ import annotations

from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.searchable_fields import (
    PermissionSearchableFields,
)
from ai.backend.manager.models.specs.querier import BulkFieldQuerier


class BulkRolePermissionQuerier(BulkFieldQuerier[PermissionRow, PermissionData]):
    """The permission entries the caller named."""

    @override
    def row_class(self) -> type[PermissionRow]:
        return PermissionRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return PermissionRow.id

    @override
    def to_data(self, row: PermissionRow) -> PermissionData:
        return PermissionSearchableFields.own.to_data(row)
