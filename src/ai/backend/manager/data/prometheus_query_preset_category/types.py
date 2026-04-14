from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class PrometheusQueryPresetCategoryData:
    """Domain model data for prometheus query preset category."""

    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


@dataclass
class PrometheusQueryPresetCategoryListResult:
    """Search result with total count for prometheus query preset categories."""

    items: list[PrometheusQueryPresetCategoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
