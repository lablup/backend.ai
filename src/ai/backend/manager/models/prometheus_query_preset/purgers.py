from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.identifier.prometheus_query_preset import PrometheusQueryPresetID
from ai.backend.manager.data.prometheus_query_preset.types import PrometheusQueryPresetData
from ai.backend.manager.models.prometheus_query_preset.row import PrometheusQueryPresetRow
from ai.backend.manager.models.specs.purger import GlobalEntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class PrometheusQueryPresetPurger(
    GlobalEntityPurger[PrometheusQueryPresetRow, PrometheusQueryPresetData]
):
    """Purger for removing a query preset from the catalog."""

    preset_id: PrometheusQueryPresetID

    @override
    def row_class(self) -> type[PrometheusQueryPresetRow]:
        return PrometheusQueryPresetRow

    @override
    def pk_value(self) -> PrometheusQueryPresetID:
        return self.preset_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: PrometheusQueryPresetRow) -> PrometheusQueryPresetData:
        return row.to_data()
