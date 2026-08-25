"""DataQuerier implementations for the prometheus query preset repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.prometheus_query_preset import PrometheusQueryPresetID
from ai.backend.manager.data.prometheus_query_preset.types import PrometheusQueryPresetData
from ai.backend.manager.models.prometheus_query_preset.row import PrometheusQueryPresetRow
from ai.backend.manager.models.specs.querier import DataQuerier


@dataclass
class PrometheusQueryPresetQuerier(
    DataQuerier[PrometheusQueryPresetRow, PrometheusQueryPresetData]
):
    preset_id: PrometheusQueryPresetID

    @override
    def row_class(self) -> type[PrometheusQueryPresetRow]:
        return PrometheusQueryPresetRow

    @override
    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return PrometheusQueryPresetRow.id

    @override
    def entity_id_value(self) -> PrometheusQueryPresetID:
        return self.preset_id

    @override
    def to_data(self, row: PrometheusQueryPresetRow) -> PrometheusQueryPresetData:
        return row.to_data()
