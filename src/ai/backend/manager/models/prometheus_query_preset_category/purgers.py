from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.identifier.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryID,
)
from ai.backend.manager.data.prometheus_query_preset_category.types import (
    PrometheusQueryPresetCategoryData,
)
from ai.backend.manager.models.prometheus_query_preset_category.row import (
    PrometheusQueryPresetCategoryRow,
)
from ai.backend.manager.models.specs.purger import EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class PrometheusQueryPresetCategoryPurger(
    EntityPurger[PrometheusQueryPresetCategoryRow, PrometheusQueryPresetCategoryData]
):
    """Purger for removing a category from the catalog."""

    category_id: PrometheusQueryPresetCategoryID

    @override
    def row_class(self) -> type[PrometheusQueryPresetCategoryRow]:
        return PrometheusQueryPresetCategoryRow

    @override
    def pk_value(self) -> PrometheusQueryPresetCategoryID:
        return self.category_id

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.category_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: PrometheusQueryPresetCategoryRow) -> PrometheusQueryPresetCategoryData:
        return row.to_data()
