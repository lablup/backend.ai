from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.prometheus_query_preset import (
    PROMETHEUS_QUERY_PRESET_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.identifier.entity import EntityID
from ai.backend.common.identifier.prometheus_query_preset import PrometheusQueryPresetID
from ai.backend.manager.actions.v2.ops.base import PurgeEntityOpsAction
from ai.backend.manager.data.prometheus_query_preset.types import PrometheusQueryPresetData
from ai.backend.manager.models.prometheus_query_preset.purgers import (
    PrometheusQueryPresetPurger,
)
from ai.backend.manager.models.prometheus_query_preset.row import PrometheusQueryPresetRow


@dataclass
class PurgePresetAction(PurgeEntityOpsAction[PrometheusQueryPresetRow, PrometheusQueryPresetData]):
    """Remove a query preset from the catalog.

    Purge-shaped: the table carries no lifecycle column, so removing one has always
    been the row leaving the table.
    """

    preset_id: PrometheusQueryPresetID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PROMETHEUS_QUERY_PRESET_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_prometheus_query_preset"

    @override
    def entity_id(self) -> EntityID:
        return self.to_purger().entity_id()

    @override
    def to_purger(self) -> PrometheusQueryPresetPurger:
        return PrometheusQueryPresetPurger(preset_id=self.preset_id)
