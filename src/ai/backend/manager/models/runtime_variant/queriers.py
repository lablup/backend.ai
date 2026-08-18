"""DataQuerier implementations for the runtime variant repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.specs.querier import DataQuerier


@dataclass
class RuntimeVariantQuerier(DataQuerier[RuntimeVariantRow, RuntimeVariantData]):
    variant_id: RuntimeVariantID

    @override
    def row_class(self) -> type[RuntimeVariantRow]:
        return RuntimeVariantRow

    @override
    def pk_value(self) -> RuntimeVariantID:
        return self.variant_id

    @override
    def to_data(self, row: RuntimeVariantRow) -> RuntimeVariantData:
        return row.to_data()
