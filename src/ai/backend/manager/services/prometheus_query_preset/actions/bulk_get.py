from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.prometheus_query_preset import PrometheusQueryPresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.prometheus_query_preset.types import PrometheusQueryPresetData
from ai.backend.manager.models.prometheus_query_preset.queriers import (
    BulkPrometheusQueryPresetQuerier,
)
from ai.backend.manager.models.prometheus_query_preset.row import PrometheusQueryPresetRow


@dataclass
class BulkGetPresetsAction(
    PartialBulkGetEntityOpsAction[PrometheusQueryPresetRow, PrometheusQueryPresetData]
):
    """Read the prometheus query presets the caller named, one permission check per preset."""

    ids: Sequence[PrometheusQueryPresetID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_prometheus_query_presets"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkPrometheusQueryPresetQuerier:
        return BulkPrometheusQueryPresetQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])
