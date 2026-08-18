from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.prometheus_query_preset import PrometheusQueryPresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import GetSingleEntityOpsAction
from ai.backend.manager.data.prometheus_query_preset.types import PrometheusQueryPresetData
from ai.backend.manager.models.prometheus_query_preset.queriers import (
    PrometheusQueryPresetQuerier,
)
from ai.backend.manager.models.prometheus_query_preset.row import PrometheusQueryPresetRow


@dataclass
class GetPresetAction(
    GetSingleEntityOpsAction[PrometheusQueryPresetRow, PrometheusQueryPresetData]
):
    """Read one query preset."""

    preset_id: PrometheusQueryPresetID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_prometheus_query_preset"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.preset_id

    @override
    def to_querier(self) -> PrometheusQueryPresetQuerier:
        return PrometheusQueryPresetQuerier(preset_id=self.preset_id)
