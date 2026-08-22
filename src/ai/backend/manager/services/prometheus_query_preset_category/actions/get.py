from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryID,
)
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import GetSingleEntityOpsAction
from ai.backend.manager.data.prometheus_query_preset_category.types import (
    PrometheusQueryPresetCategoryData,
)
from ai.backend.manager.models.prometheus_query_preset_category.queriers import (
    PrometheusQueryPresetCategoryQuerier,
)
from ai.backend.manager.models.prometheus_query_preset_category.row import (
    PrometheusQueryPresetCategoryRow,
)


@dataclass
class GetCategoryAction(
    GetSingleEntityOpsAction[PrometheusQueryPresetCategoryRow, PrometheusQueryPresetCategoryData]
):
    """Read one category from the catalog."""

    category_id: PrometheusQueryPresetCategoryID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_prometheus_query_preset_category"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.category_id

    @override
    def to_querier(self) -> PrometheusQueryPresetCategoryQuerier:
        return PrometheusQueryPresetCategoryQuerier(category_id=self.category_id)
