from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.prometheus_query_preset_category import (
    PROMETHEUS_QUERY_PRESET_CATEGORY_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.prometheus_query_preset_category.types import (
    PrometheusQueryPresetCategoryData,
)
from ai.backend.manager.models.prometheus_query_preset_category.row import (
    PrometheusQueryPresetCategoryRow,
)
from ai.backend.manager.repositories.prometheus_query_preset_category.searchers import (
    PrometheusQueryPresetCategorySearcher,
)


@dataclass
class SearchCategoriesAction(
    SearchGlobalOpsAction[PrometheusQueryPresetCategoryRow, PrometheusQueryPresetCategoryData]
):
    """Page through the category catalog."""

    searcher: PrometheusQueryPresetCategorySearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PROMETHEUS_QUERY_PRESET_CATEGORY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_prometheus_query_preset_categories"

    @override
    def to_searcher(self) -> PrometheusQueryPresetCategorySearcher:
        return self.searcher
