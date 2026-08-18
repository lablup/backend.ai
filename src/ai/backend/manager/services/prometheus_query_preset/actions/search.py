from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.prometheus_query_preset import (
    PROMETHEUS_QUERY_PRESET_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.prometheus_query_preset.types import PrometheusQueryPresetData
from ai.backend.manager.models.prometheus_query_preset.row import PrometheusQueryPresetRow
from ai.backend.manager.models.prometheus_query_preset.searchers import (
    PrometheusQueryPresetSearcher,
)


@dataclass
class SearchPresetsAction(
    SearchGlobalOpsAction[PrometheusQueryPresetRow, PrometheusQueryPresetData]
):
    """Page through the query preset catalog."""

    searcher: PrometheusQueryPresetSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PROMETHEUS_QUERY_PRESET_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_prometheus_query_presets"

    @override
    def to_searcher(self) -> PrometheusQueryPresetSearcher:
        return self.searcher
