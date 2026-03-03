from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.manager.types import OptionalState, PartialModifier, TriState


@dataclass(frozen=True)
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


@dataclass
class PrometheusQueryPresetModifier(PartialModifier):
    """Modifier for prometheus query preset."""

    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    metric_name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    query_template: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    time_window: TriState[str] = field(default_factory=TriState[str].nop)
    filter_labels: OptionalState[list[str]] = field(default_factory=OptionalState[list[str]].nop)
    group_labels: OptionalState[list[str]] = field(default_factory=OptionalState[list[str]].nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.metric_name.update_dict(to_update, "metric_name")
        self.query_template.update_dict(to_update, "query_template")
        self.time_window.update_dict(to_update, "time_window")
        self.filter_labels.update_dict(to_update, "filter_labels")
        self.group_labels.update_dict(to_update, "group_labels")
        return to_update


@dataclass
class PrometheusQueryPresetListResult:
    """Search result with total count for prometheus query presets."""

    items: list[PrometheusQueryPresetData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
