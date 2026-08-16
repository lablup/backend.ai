from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryID,
)
from ai.backend.manager.data.prometheus_query_preset.types import PrometheusQueryPresetData
from ai.backend.manager.models.prometheus_query_preset.row import (
    PresetOptions,
    PrometheusQueryPresetRow,
)
from ai.backend.manager.models.specs.creator import GlobalEntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class PrometheusQueryPresetCreator(
    GlobalEntityCreator[PrometheusQueryPresetRow, PrometheusQueryPresetData]
):
    """Creator for a query preset in the global catalog."""

    name: str
    metric_name: str
    query_template: str
    time_window: str | None
    filter_labels: list[str]
    group_labels: list[str]
    description: str | None = None
    rank: int = 0
    category_id: PrometheusQueryPresetCategoryID | None = None

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> PrometheusQueryPresetRow:
        return PrometheusQueryPresetRow(
            name=self.name,
            description=self.description,
            rank=self.rank,
            category_id=self.category_id,
            metric_name=self.metric_name,
            query_template=self.query_template,
            time_window=self.time_window,
            options=PresetOptions(
                filter_labels=self.filter_labels,
                group_labels=self.group_labels,
            ),
        )

    @override
    def to_data(self, row: PrometheusQueryPresetRow) -> PrometheusQueryPresetData:
        return row.to_data()
