"""Prometheus query preset GQL payload and result types."""

from __future__ import annotations

import strawberry
from strawberry import ID


@strawberry.type(name="PrometheusPresetOptions", description="Preset options for label governance.")
class PrometheusPresetOptionsGQL:
    filter_labels: list[str] = strawberry.field(description="Allowed filter label keys.")
    group_labels: list[str] = strawberry.field(description="Allowed group-by label keys.")


@strawberry.type(
    name="MetricLabelEntry", description="Key-value label entry from Prometheus result."
)
class MetricLabelEntryGQL:
    key: str
    value: str


@strawberry.type(
    name="MetricResultValue", description="Single timestamp-value pair from Prometheus."
)
class MetricResultValueGQL:
    timestamp: float
    value: str


@strawberry.type(name="MetricResult", description="Single metric result from Prometheus query.")
class MetricResultGQL:
    metric: list[MetricLabelEntryGQL] = strawberry.field(
        description="Metric labels as key-value entries."
    )
    values: list[MetricResultValueGQL] = strawberry.field(description="Time-series values.")


@strawberry.type(
    name="PrometheusQueryResult", description="Result from executing a prometheus query preset."
)
class PrometheusQueryResultGQL:
    status: str = strawberry.field(description="Prometheus response status.")
    result_type: str = strawberry.field(description="Result type (e.g., matrix).")
    result: list[MetricResultGQL] = strawberry.field(description="Metric result entries.")


@strawberry.type(
    name="DeletePrometheusQueryPresetPayload",
    description="Payload returned after deleting a preset.",
)
class DeletePrometheusQueryPresetPayload:
    id: ID = strawberry.field(description="ID of the deleted preset.")
