from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.prometheus_query_preset_category.types import (
    PrometheusQueryPresetCategoryData,
)
from ai.backend.manager.models.prometheus_query_preset_category.row import (
    PrometheusQueryPresetCategoryRow,
)
from ai.backend.manager.models.specs.creator import GlobalEntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class PrometheusQueryPresetCategoryCreator(
    GlobalEntityCreator[PrometheusQueryPresetCategoryRow, PrometheusQueryPresetCategoryData]
):
    """Creator for a category in the global preset catalog."""

    name: str
    description: str | None

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        # The name is unique in the schema, but no domain error was ever mapped to that
        # violation — leaving it unmapped keeps the response the caller already gets.
        return ()

    @override
    def build_row(self) -> PrometheusQueryPresetCategoryRow:
        return PrometheusQueryPresetCategoryRow(name=self.name, description=self.description)

    @override
    def to_data(self, row: PrometheusQueryPresetCategoryRow) -> PrometheusQueryPresetCategoryData:
        return row.to_data()
