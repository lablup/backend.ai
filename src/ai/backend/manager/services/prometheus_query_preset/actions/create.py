from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.prometheus_query_preset import (
    PROMETHEUS_QUERY_PRESET_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import CreateGlobalOpsAction
from ai.backend.manager.data.prometheus_query_preset.types import PrometheusQueryPresetData
from ai.backend.manager.models.prometheus_query_preset.creators import (
    PrometheusQueryPresetCreator,
)
from ai.backend.manager.models.prometheus_query_preset.row import PrometheusQueryPresetRow


@dataclass
class CreatePresetAction(
    CreateGlobalOpsAction[PrometheusQueryPresetRow, PrometheusQueryPresetData]
):
    """Add a query preset to the global catalog."""

    creator: PrometheusQueryPresetCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PROMETHEUS_QUERY_PRESET_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_prometheus_query_preset"

    @override
    def to_creator(self) -> PrometheusQueryPresetCreator:
        return self.creator
