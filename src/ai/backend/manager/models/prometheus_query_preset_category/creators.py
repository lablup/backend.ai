from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryID,
)
from ai.backend.manager.data.prometheus_query_preset_category.types import (
    PrometheusQueryPresetCategoryData,
)
from ai.backend.manager.models.prometheus_query_preset_category.row import (
    PrometheusQueryPresetCategoryRow,
)
from ai.backend.manager.models.prometheus_query_preset_category.searchable_fields import (
    PrometheusQueryPresetCategorySearchableFields,
)
from ai.backend.manager.models.specs.created_in import CreatedInPublic
from ai.backend.manager.models.specs.creator import EntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class PrometheusQueryPresetCategoryCreator(
    CreatedInPublic[PrometheusQueryPresetCategoryRow],
    EntityCreator[PrometheusQueryPresetCategoryRow, PrometheusQueryPresetCategoryData],
):
    """Creator for a category in the global preset catalog."""

    name: str
    description: str | None

    @override
    def entity_id(self, row: PrometheusQueryPresetCategoryRow) -> PrometheusQueryPresetCategoryID:
        return PrometheusQueryPresetCategoryID(row.id)

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
        return PrometheusQueryPresetCategorySearchableFields.own.to_data(row)
