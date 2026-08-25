from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.prometheus_query_preset import PrometheusQueryPresetID
from ai.backend.common.data.entity.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryID,
)
from ai.backend.manager.data.prometheus_query_preset.types import PrometheusQueryPresetData
from ai.backend.manager.models.prometheus_query_preset.row import (
    PresetOptions,
    PrometheusQueryPresetRow,
)
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class PrometheusQueryPresetUpdater(
    DataUpdater[PrometheusQueryPresetRow, PrometheusQueryPresetData]
):
    """Retune a stored preset.

    ``filter_labels`` and ``group_labels`` share the JSONB ``options`` column, so
    updating one alone writes it with ``jsonb_set`` and leaves the other as stored.
    """

    preset_id: PrometheusQueryPresetID
    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    description: TriState[str] = field(default_factory=TriState[str].nop)
    rank: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    category_id: TriState[PrometheusQueryPresetCategoryID] = field(
        default_factory=TriState[PrometheusQueryPresetCategoryID].nop
    )
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
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return PrometheusQueryPresetRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.preset_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.description.update_dict(to_update, "description")
        self.rank.update_dict(to_update, "rank")
        self.category_id.update_dict(to_update, "category_id")
        self.metric_name.update_dict(to_update, "metric_name")
        self.query_template.update_dict(to_update, "query_template")
        self.time_window.update_dict(to_update, "time_window")
        options = self._build_options()
        if options is not None:
            to_update["options"] = options
        return to_update

    @override
    def to_data(self, row: PrometheusQueryPresetRow) -> PrometheusQueryPresetData:
        return row.to_data()

    def _build_options(self) -> Any:
        filter_value = self.filter_labels.optional_value()
        group_value = self.group_labels.optional_value()
        if filter_value is not None and group_value is not None:
            return PresetOptions(filter_labels=filter_value, group_labels=group_value)
        if filter_value is not None:
            return self._set_option_key("filter_labels", filter_value)
        if group_value is not None:
            return self._set_option_key("group_labels", group_value)
        return None

    def _set_option_key(self, key: str, value: list[str]) -> sa.sql.elements.ColumnElement[Any]:
        return sa.func.jsonb_set(
            PrometheusQueryPresetRow.options,
            sa.cast([key], pgsql.ARRAY(sa.Text)),
            sa.cast(value, pgsql.JSONB),
        )
