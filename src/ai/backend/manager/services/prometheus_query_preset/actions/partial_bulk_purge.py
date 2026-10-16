from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.prometheus_query_preset import PrometheusQueryPresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkPurgeEntityOpsAction
from ai.backend.manager.data.prometheus_query_preset.types import PrometheusQueryPresetData
from ai.backend.manager.models.prometheus_query_preset.purgers import (
    PrometheusQueryPresetPurger,
)
from ai.backend.manager.models.prometheus_query_preset.row import PrometheusQueryPresetRow


@dataclass(frozen=True)
class PartialBulkPurgePresetsAction(
    PartialBulkPurgeEntityOpsAction[PrometheusQueryPresetRow, PrometheusQueryPresetData]
):
    """Remove the named presets from the catalog, answering for each one."""

    ids: Sequence[PrometheusQueryPresetID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_purge_prometheus_query_presets"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_purgers(self) -> Mapping[EntityIdentifier, PrometheusQueryPresetPurger]:
        return {
            preset_id: PrometheusQueryPresetPurger(preset_id=preset_id) for preset_id in self.ids
        }

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[preset_id for preset_id in self.ids if preset_id in allowed])
