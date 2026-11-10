from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import override

from ai.backend.common.data.entity.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryID,
)
from ai.backend.common.data.entity.types import EntityData, EntityIdentifier


@dataclass(frozen=True)
class PrometheusQueryPresetCategoryData(EntityData):
    """Domain model data for prometheus query preset category."""

    id: PrometheusQueryPresetCategoryID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.id


@dataclass
class PrometheusQueryPresetCategoryListResult:
    """Search result with total count for prometheus query preset categories."""

    items: list[PrometheusQueryPresetCategoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
