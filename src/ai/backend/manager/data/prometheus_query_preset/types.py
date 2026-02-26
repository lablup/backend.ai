from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.manager.types import OptionalState, PartialModifier, TriState


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
        filter_value = self.filter_labels.optional_value()
        group_value = self.group_labels.optional_value()
        if filter_value is not None or group_value is not None:
            # options is stored as a single JSONB column via PydanticColumn
            # We need to reconstruct the full options dict for partial updates
            to_update["_filter_labels"] = filter_value
            to_update["_group_labels"] = group_value
        return to_update


@dataclass
class PrometheusQueryPresetListResult:
    """Search result with total count for prometheus query presets."""

    items: list[PrometheusQueryPresetData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
