"""CreatorSpec implementations for prometheus query preset repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.models.prometheus_query_preset.row import (
    PresetOptions,
    PrometheusQueryPresetRow,
)
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class PrometheusQueryPresetCreatorSpec(CreatorSpec[PrometheusQueryPresetRow]):
    """CreatorSpec for prometheus query preset."""

    name: str
    metric_name: str
    query_template: str
    time_window: str | None
    filter_labels: list[str]
    group_labels: list[str]

    @override
    def build_row(self) -> PrometheusQueryPresetRow:
        return PrometheusQueryPresetRow(
            name=self.name,
            metric_name=self.metric_name,
            query_template=self.query_template,
            time_window=self.time_window,
            options=PresetOptions(
                filter_labels=self.filter_labels,
                group_labels=self.group_labels,
            ),
        )
