"""DataQuerier implementations for the role repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.role import RoleID
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.specs.querier import DataQuerier


@dataclass
class RoleQuerier(DataQuerier[RoleRow, RoleData]):
    role_id: RoleID

    @override
    def row_class(self) -> type[RoleRow]:
        return RoleRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return RoleRow.id

    @override
    def entity_id_value(self) -> RoleID:
        return self.role_id

    @override
    def to_data(self, row: RoleRow) -> RoleData:
        return row.to_data()
