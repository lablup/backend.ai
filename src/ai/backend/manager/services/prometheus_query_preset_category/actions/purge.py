from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.prometheus_query_preset_category import (
    PROMETHEUS_QUERY_PRESET_CATEGORY_ENTITY_TYPE,
    PrometheusQueryPresetCategoryID,
)
from ai.backend.common.data.entity.types import EntityID, EntityType
from ai.backend.manager.actions.v2.ops.base import PurgeEntityOpsAction
from ai.backend.manager.data.prometheus_query_preset_category.types import (
    PrometheusQueryPresetCategoryData,
)
from ai.backend.manager.models.prometheus_query_preset_category.purgers import (
    PrometheusQueryPresetCategoryPurger,
)
from ai.backend.manager.models.prometheus_query_preset_category.row import (
    PrometheusQueryPresetCategoryRow,
)


@dataclass
class PurgeCategoryAction(
    PurgeEntityOpsAction[PrometheusQueryPresetCategoryRow, PrometheusQueryPresetCategoryData]
):
    """Remove a category from the catalog.

    Purge-shaped: the table carries no lifecycle column, so removing one has always
    been the row leaving the table.
    """

    category_id: PrometheusQueryPresetCategoryID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PROMETHEUS_QUERY_PRESET_CATEGORY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_prometheus_query_preset_category"

    @override
    def entity_id(self) -> EntityID:
        return self.to_purger().entity_id()

    @override
    def to_purger(self) -> PrometheusQueryPresetCategoryPurger:
        return PrometheusQueryPresetCategoryPurger(category_id=self.category_id)
