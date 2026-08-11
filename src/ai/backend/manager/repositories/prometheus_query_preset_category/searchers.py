"""Searcher implementations for the prometheus query preset category repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.prometheus_query_preset_category.types import (
    PrometheusQueryPresetCategoryData,
)
from ai.backend.manager.models.prometheus_query_preset_category.row import (
    PrometheusQueryPresetCategoryRow,
)
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class PrometheusQueryPresetCategorySearcher(
    Searcher[PrometheusQueryPresetCategoryRow, PrometheusQueryPresetCategoryData]
):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(PrometheusQueryPresetCategoryRow)

    @override
    def to_data(self, row: PrometheusQueryPresetCategoryRow) -> PrometheusQueryPresetCategoryData:
        return row.to_data()
