"""DataQuerier implementations for the role preset repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.specs.querier import DataQuerier


@dataclass
class RolePresetQuerier(DataQuerier[RolePresetRow, RolePresetData]):
    preset_id: RolePresetID

    @override
    def row_class(self) -> type[RolePresetRow]:
        return RolePresetRow

    @override
    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return RolePresetRow.id

    @override
    def entity_id_value(self) -> RolePresetID:
        return self.preset_id

    @override
    def to_data(self, row: RolePresetRow) -> RolePresetData:
        return row.to_data()
