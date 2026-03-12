"""Prometheus query preset GQL input types."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

import strawberry
from strawberry import UNSET

from ai.backend.common.dto.clients.prometheus.request import QueryTimeRange
from ai.backend.manager.data.prometheus_query_preset import ExecutePresetOptions
from ai.backend.manager.models.prometheus_query_preset import PrometheusQueryPresetRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.prometheus_query_preset.creators import (
    PrometheusQueryPresetCreatorSpec,
)
from ai.backend.manager.repositories.prometheus_query_preset.updaters import (
    PrometheusQueryPresetUpdaterSpec,
)
from ai.backend.manager.types import OptionalState, TriState


@strawberry.input(
    name="QueryDefinitionOptionsInput",
    description="Added in 26.3.0. Options for query definition labels.",
)
class QueryDefinitionOptionsInput:
    filter_labels: list[str] = strawberry.field(description="Allowed filter label keys.")
    group_labels: list[str] = strawberry.field(description="Allowed group-by label keys.")


@strawberry.input(
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

    def to_creator(self) -> Creator[PrometheusQueryPresetRow]:
        return Creator(
            spec=PrometheusQueryPresetCreatorSpec(
                name=self.name,
                metric_name=self.metric_name,
                query_template=self.query_template,
                time_window=self.time_window,
                filter_labels=self.options.filter_labels,
                group_labels=self.options.group_labels,
            )
        )


@strawberry.input(
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

    def to_updater(self, preset_id: UUID) -> Updater[PrometheusQueryPresetRow]:
        spec = PrometheusQueryPresetUpdaterSpec(
            name=OptionalState[str].from_graphql(self.name),
            metric_name=OptionalState[str].from_graphql(self.metric_name),
            query_template=OptionalState[str].from_graphql(self.query_template),
            time_window=TriState[str].from_graphql(self.time_window),
        )

        if self.options is not UNSET and self.options is not None:
            spec.filter_labels = OptionalState.update(self.options.filter_labels)
            spec.group_labels = OptionalState.update(self.options.group_labels)

        return Updater(pk_value=preset_id, spec=spec)


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
