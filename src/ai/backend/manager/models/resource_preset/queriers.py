"""DataQuerier implementations for the resource presets table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.resource_preset import ResourcePresetID
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.specs.querier import DataQuerier


@dataclass
class ResourcePresetQuerier(DataQuerier[ResourcePresetRow, ResourcePresetData]):
    """Reads the preset an id names."""

    preset_id: ResourcePresetID

    @override
    def row_class(self) -> type[ResourcePresetRow]:
        return ResourcePresetRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return ResourcePresetRow.id

    @override
    def entity_id_value(self) -> ResourcePresetID:
        return self.preset_id

    @override
    def to_data(self, row: ResourcePresetRow) -> ResourcePresetData:
        return row.to_dataclass()
