"""DataQuerier implementations for the runtime variant preset repository."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.models.specs.querier import DataQuerier


@dataclass
class RuntimeVariantPresetQuerier(DataQuerier[RuntimeVariantPresetRow, RuntimeVariantPresetData]):
    preset_id: uuid.UUID

    @override
    def row_class(self) -> type[RuntimeVariantPresetRow]:
        return RuntimeVariantPresetRow

    @override
    def pk_value(self) -> uuid.UUID:
        return self.preset_id

    @override
    def to_data(self, row: RuntimeVariantPresetRow) -> RuntimeVariantPresetData:
        return row.to_data()
