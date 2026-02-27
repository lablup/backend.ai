"""UpdaterSpec implementations for prometheus query preset repository."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.models.prometheus_query_preset.row import (
    PresetOptions,
    PrometheusQueryPresetRow,
)
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class PrometheusQueryPresetUpdaterSpec(UpdaterSpec[PrometheusQueryPresetRow]):
    """UpdaterSpec for prometheus query preset updates."""

    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    metric_name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    query_template: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    time_window: TriState[str] = field(default_factory=TriState[str].nop)
    filter_labels: OptionalState[list[str]] = field(default_factory=OptionalState[list[str]].nop)
    group_labels: OptionalState[list[str]] = field(default_factory=OptionalState[list[str]].nop)

    @property
    @override
    def row_class(self) -> type[PrometheusQueryPresetRow]:
        return PrometheusQueryPresetRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.metric_name.update_dict(to_update, "metric_name")
        self.query_template.update_dict(to_update, "query_template")
        self.time_window.update_dict(to_update, "time_window")
        filter_value = self.filter_labels.optional_value()
        group_value = self.group_labels.optional_value()
        if filter_value is not None or group_value is not None:
            # Reconstruct options as a PresetOptions model for PydanticColumn
            to_update["options"] = PresetOptions(
                filter_labels=filter_value if filter_value is not None else [],
                group_labels=group_value if group_value is not None else [],
            )
        return to_update
