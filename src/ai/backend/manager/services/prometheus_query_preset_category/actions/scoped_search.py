"""Preset category search over the scopes a category is reachable from."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryEntityType,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import ScopedSearchOpsAction
from ai.backend.manager.data.prometheus_query_preset_category.types import (
    PrometheusQueryPresetCategoryData,
)
from ai.backend.manager.models.prometheus_query_preset_category.row import (
    PrometheusQueryPresetCategoryRow,
)

__all__ = ("ScopedSearchCategoriesAction",)


@dataclass(frozen=True)
class ScopedSearchCategoriesAction(
    ScopedSearchOpsAction[PrometheusQueryPresetCategoryRow, PrometheusQueryPresetCategoryData]
):
    """Page through the preset categories the named scopes reach, combined with OR.

    Every scope is authorized and every using entity must be readable before the read
    runs, so a caller reaching for one they cannot see is refused rather than served the
    rest.
    """

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PrometheusQueryPresetCategoryEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_prometheus_query_preset_categories"
