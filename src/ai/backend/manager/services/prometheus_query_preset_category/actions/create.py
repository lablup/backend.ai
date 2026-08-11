from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.prometheus_query_preset_category import (
    PROMETHEUS_QUERY_PRESET_CATEGORY_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import CreateGlobalOpsAction
from ai.backend.manager.data.prometheus_query_preset_category.types import (
    PrometheusQueryPresetCategoryData,
)
from ai.backend.manager.models.prometheus_query_preset_category.creators import (
    PrometheusQueryPresetCategoryCreator,
)
from ai.backend.manager.models.prometheus_query_preset_category.row import (
    PrometheusQueryPresetCategoryRow,
)


@dataclass
class CreateCategoryAction(
    CreateGlobalOpsAction[PrometheusQueryPresetCategoryRow, PrometheusQueryPresetCategoryData]
):
    """Add a category to the global preset catalog."""

    creator: PrometheusQueryPresetCategoryCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PROMETHEUS_QUERY_PRESET_CATEGORY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_prometheus_query_preset_category"

    @override
    def to_creator(self) -> PrometheusQueryPresetCategoryCreator:
        return self.creator
