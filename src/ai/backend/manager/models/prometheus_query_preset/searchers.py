"""Searcher implementations for the prometheus query preset repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.prometheus_query_preset.types import PrometheusQueryPresetData
from ai.backend.manager.models.prometheus_query_preset.row import PrometheusQueryPresetRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class PrometheusQueryPresetSearcher(Searcher[PrometheusQueryPresetRow, PrometheusQueryPresetData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(PrometheusQueryPresetRow)

    @override
    def to_data(self, row: PrometheusQueryPresetRow) -> PrometheusQueryPresetData:
        return row.to_data()
