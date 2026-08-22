"""DataQuerier implementations for the prometheus query preset category repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryID,
)
from ai.backend.manager.data.prometheus_query_preset_category.types import (
    PrometheusQueryPresetCategoryData,
)
from ai.backend.manager.models.prometheus_query_preset_category.row import (
    PrometheusQueryPresetCategoryRow,
)
from ai.backend.manager.models.specs.querier import DataQuerier


@dataclass
class PrometheusQueryPresetCategoryQuerier(
    DataQuerier[PrometheusQueryPresetCategoryRow, PrometheusQueryPresetCategoryData]
):
    category_id: PrometheusQueryPresetCategoryID

    @override
    def row_class(self) -> type[PrometheusQueryPresetCategoryRow]:
        return PrometheusQueryPresetCategoryRow

    @override
    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return PrometheusQueryPresetCategoryRow.id

    @override
    def entity_id_value(self) -> PrometheusQueryPresetCategoryID:
        return self.category_id

    @override
    def to_data(self, row: PrometheusQueryPresetCategoryRow) -> PrometheusQueryPresetCategoryData:
        return row.to_data()
