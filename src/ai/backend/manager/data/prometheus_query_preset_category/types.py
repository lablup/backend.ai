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
