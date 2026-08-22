"""DataQuerier implementations for the runtime variant preset repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.runtime_variant_preset import RuntimeVariantPresetID
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.models.specs.querier import DataQuerier


@dataclass
class RuntimeVariantPresetQuerier(DataQuerier[RuntimeVariantPresetRow, RuntimeVariantPresetData]):
    preset_id: RuntimeVariantPresetID

    @override
    def row_class(self) -> type[RuntimeVariantPresetRow]:
        return RuntimeVariantPresetRow

    @override
    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return RuntimeVariantPresetRow.id

    @override
    def entity_id_value(self) -> RuntimeVariantPresetID:
        return self.preset_id

    @override
    def to_data(self, row: RuntimeVariantPresetRow) -> RuntimeVariantPresetData:
        return row.to_data()
