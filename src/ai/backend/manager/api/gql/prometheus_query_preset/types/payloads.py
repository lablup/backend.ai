"""Prometheus query preset GQL payload and result types."""

from __future__ import annotations

import strawberry
from strawberry import ID


@strawberry.type(
    name="QueryDefinitionOptions",
    description="Added in 26.3.0. Options for query definition label governance.",
)
class PrometheusPresetOptionsGQL:
    filter_labels: list[str] = strawberry.field(description="Allowed filter label keys.")
    group_labels: list[str] = strawberry.field(description="Allowed group-by label keys.")


@strawberry.type(
    name="MetricLabelEntry",
    description="Added in 26.3.0. Key-value label entry from Prometheus result.",
)
class MetricLabelEntryGQL:
    key: str
    value: str


@strawberry.type(
    name="MetricResultValue",
    description="Added in 26.3.0. Single timestamp-value pair from Prometheus.",
)
class MetricResultValueGQL:
    timestamp: float
    value: str


@strawberry.type(
    name="MetricResult",
    description="Added in 26.3.0. Single metric result from Prometheus query.",
)
class MetricResultGQL:
    metric: list[MetricLabelEntryGQL] = strawberry.field(
        description="Metric labels as key-value entries."
    )
    values: list[MetricResultValueGQL] = strawberry.field(description="Time-series values.")


@strawberry.type(
    name="QueryDefinitionExecuteResult",
    description="Added in 26.3.0. Result from executing a query definition.",
)
class PrometheusQueryResultGQL:
    status: str = strawberry.field(description="Prometheus response status.")
    result_type: str = strawberry.field(description="Result type (e.g., matrix).")
    result: list[MetricResultGQL] = strawberry.field(description="Metric result entries.")


@strawberry.type(
    name="DeleteQueryDefinitionPayload",
    description="Added in 26.3.0. Payload returned after deleting a query definition.",
)
class DeletePrometheusQueryPresetPayload:
    id: ID = strawberry.field(description="ID of the deleted query definition.")
