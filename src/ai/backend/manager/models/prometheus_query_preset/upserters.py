from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.prometheus_query_preset import PrometheusQueryPresetID
from ai.backend.common.data.entity.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryID,
)
from ai.backend.manager.data.prometheus_query_preset.types import PrometheusQueryPresetData
from ai.backend.manager.models.prometheus_query_preset.row import (
    PresetOptions,
    PrometheusQueryPresetRow,
)
from ai.backend.manager.models.prometheus_query_preset.searchable_fields import (
    PrometheusQueryPresetSearchableFields,
)
from ai.backend.manager.models.specs.created_in import CreatedInPublic
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter

__all__ = ("PrometheusQueryPresetUpserter",)


@dataclass
class PrometheusQueryPresetUpserter(
    CreatedInPublic[PrometheusQueryPresetRow],
    EntityUpserter[PrometheusQueryPresetRow, PrometheusQueryPresetData],
):
    """Write a query preset under its stated id. Conflict key: id."""

    id: PrometheusQueryPresetID
    name: str
    metric_name: str
    query_template: str
    time_window: str | None
    options: PresetOptions
    description: str | None
    rank: int
    category_id: PrometheusQueryPresetCategoryID | None

    @override
    def entity_id(self, row: PrometheusQueryPresetRow) -> PrometheusQueryPresetID:
        return PrometheusQueryPresetID(row.id)

    @override
    def row_class(self) -> type[PrometheusQueryPresetRow]:
        return PrometheusQueryPresetRow

    @override
    def index_elements(self) -> list[str]:
        return ["id"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"id": self.id, **self._values()}

    @override
    def build_update_values(self) -> dict[str, Any]:
        """``updated_at`` is set here: ``ON CONFLICT DO UPDATE`` bypasses the ORM's
        ``onupdate``."""
        return {**self._values(), "updated_at": sa.func.now()}

    def _values(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "metric_name": self.metric_name,
            "query_template": self.query_template,
            "time_window": self.time_window,
            "options": self.options,
            "description": self.description,
            "rank": self.rank,
            "category_id": self.category_id,
        }

    @override
    def to_data(self, row: PrometheusQueryPresetRow) -> PrometheusQueryPresetData:
        return PrometheusQueryPresetSearchableFields.own.to_data(row)
