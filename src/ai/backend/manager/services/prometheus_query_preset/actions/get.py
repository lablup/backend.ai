from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.prometheus_query_preset import (
    PROMETHEUS_QUERY_PRESET_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.identifier.prometheus_query_preset import PrometheusQueryPresetID
from ai.backend.manager.actions.v2.ops.base import GetGlobalOpsAction
from ai.backend.manager.data.prometheus_query_preset.types import PrometheusQueryPresetData
from ai.backend.manager.models.prometheus_query_preset.row import PrometheusQueryPresetRow
from ai.backend.manager.repositories.prometheus_query_preset.queriers import (
    PrometheusQueryPresetQuerier,
)


@dataclass
class GetPresetAction(GetGlobalOpsAction[PrometheusQueryPresetRow, PrometheusQueryPresetData]):
    """Read one query preset."""

    preset_id: PrometheusQueryPresetID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PROMETHEUS_QUERY_PRESET_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_prometheus_query_preset"

    @override
    def to_querier(self) -> PrometheusQueryPresetQuerier:
        return PrometheusQueryPresetQuerier(preset_id=self.preset_id)
