"""Prometheus query preset GQL input types."""

from __future__ import annotations

from datetime import datetime

import strawberry
from strawberry import UNSET

from ai.backend.common.api_handlers import SENTINEL
from ai.backend.common.dto.clients.prometheus.request import QueryTimeRange
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    CreateQueryDefinitionInput as CreateQueryDefinitionInputDTO,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    CreateQueryDefinitionOptionsInput as CreateQueryDefinitionOptionsInputDTO,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    ModifyQueryDefinitionInput as ModifyQueryDefinitionInputDTO,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    ModifyQueryDefinitionOptionsInput as ModifyQueryDefinitionOptionsInputDTO,
)
from ai.backend.manager.data.prometheus_query_preset import ExecutePresetOptions


@strawberry.experimental.pydantic.input(
    model=CreateQueryDefinitionOptionsInputDTO,
    name="QueryDefinitionOptionsInput",
    description="Added in 26.3.0. Options for query definition labels.",
)
class QueryDefinitionOptionsInput:
    filter_labels: list[str] = strawberry.field(description="Allowed filter label keys.")
    group_labels: list[str] = strawberry.field(description="Allowed group-by label keys.")


@strawberry.experimental.pydantic.input(
    model=CreateQueryDefinitionInputDTO,
    name="CreateQueryDefinitionInput",
    description="Added in 26.3.0. Input for creating a new query definition.",
)
class CreateQueryDefinitionInput:
    name: str = strawberry.field(description="Human-readable identifier (must be unique).")
    metric_name: str = strawberry.field(description="Prometheus metric name.")
    query_template: str = strawberry.field(
        description="PromQL template with {labels}, {window}, {group_by} placeholders."
    )
    time_window: str | None = strawberry.field(default=None, description="Default time window.")
    options: QueryDefinitionOptionsInput = strawberry.field(
        description="Query definition options including filter and group labels."
    )


@strawberry.experimental.pydantic.input(
    model=ModifyQueryDefinitionInputDTO,
    name="ModifyQueryDefinitionInput",
    description="Added in 26.3.0. Input for modifying an existing query definition.",
)
class ModifyQueryDefinitionInput:
    name: str | None = strawberry.field(default=UNSET, description="New name.")
    metric_name: str | None = strawberry.field(default=UNSET, description="New metric name.")
    query_template: str | None = strawberry.field(default=UNSET, description="New PromQL template.")
    time_window: str | None = strawberry.field(
        default=UNSET, description="New default time window."
    )
    options: QueryDefinitionOptionsInput | None = strawberry.field(
        default=UNSET, description="New query definition options."
    )

    def to_pydantic(self) -> ModifyQueryDefinitionInputDTO:
        return ModifyQueryDefinitionInputDTO(
            name=None if self.name is UNSET else self.name,
            metric_name=None if self.metric_name is UNSET else self.metric_name,
            query_template=None if self.query_template is UNSET else self.query_template,
            time_window=SENTINEL if self.time_window is UNSET else self.time_window,
            options=None
            if (self.options is UNSET or self.options is None)
            else ModifyQueryDefinitionOptionsInputDTO(
                filter_labels=self.options.filter_labels,
                group_labels=self.options.group_labels,
            ),
        )


@strawberry.input(
    name="QueryTimeRangeInput",
    description="Added in 26.3.0. Time range for Prometheus query.",
)
class QueryTimeRangeInput:
    start: datetime = strawberry.field(description="Start of the time range.")
    end: datetime = strawberry.field(description="End of the time range.")
    step: str = strawberry.field(description="Query resolution step (e.g., '60s').")

    def to_internal(self) -> QueryTimeRange:
        return QueryTimeRange(
            start=self.start.isoformat(),
            end=self.end.isoformat(),
            step=self.step,
        )


@strawberry.input(
    name="MetricLabelEntryInput",
    description="Added in 26.3.0. Key-value label entry for queries.",
)
class MetricLabelEntryInput:
    key: str = strawberry.field(description="Label key.")
    value: str = strawberry.field(description="Label value.")


@strawberry.input(
    name="ExecuteQueryDefinitionOptionsInput",
    description="Added in 26.3.0. Options for executing a query definition.",
)
class ExecuteQueryDefinitionOptionsInput:
    filter_labels: list[MetricLabelEntryInput] | None = strawberry.field(
        default=None, description="Label key-value pairs to filter by."
    )
    group_labels: list[str] | None = strawberry.field(
        default=None, description="Label keys to group results by."
    )

    def to_internal(self) -> ExecutePresetOptions:
        filter_labels: dict[str, str] = {}
        if self.filter_labels:
            for entry in self.filter_labels:
                filter_labels[entry.key] = entry.value
        return ExecutePresetOptions(
            filter_labels=filter_labels,
            group_labels=self.group_labels or [],
        )
