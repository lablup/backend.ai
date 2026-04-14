"""CreatorSpec implementations for prometheus query preset category repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.models.prometheus_query_preset_category.row import (
    PrometheusQueryPresetCategoryRow,
)
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class PrometheusQueryPresetCategoryCreatorSpec(CreatorSpec[PrometheusQueryPresetCategoryRow]):
    """CreatorSpec for prometheus query preset category."""

    name: str
    description: str | None

    @override
    def build_row(self) -> PrometheusQueryPresetCategoryRow:
        return PrometheusQueryPresetCategoryRow(
            name=self.name,
            description=self.description,
        )
