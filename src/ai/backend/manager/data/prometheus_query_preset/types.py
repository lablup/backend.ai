from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass
class PrometheusQueryPresetData:
    """Domain model data for prometheus query preset."""

    id: UUID
    name: str
    metric_name: str
    query_template: str
    time_window: str | None
    filter_labels: list[str]
    group_labels: list[str]
    created_at: datetime = field(compare=False)
    updated_at: datetime = field(compare=False)
