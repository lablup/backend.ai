"""Prometheus query preset GQL payload and result types."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

import strawberry
from strawberry import ID

if TYPE_CHECKING:
    from ai.backend.common.dto.clients.prometheus.response import MetricResponse


@strawberry.type(
    name="QueryDefinitionOptions",
    description="Added in 26.3.0. Options for query definition label governance.",
)
class QueryDefinitionOptionsGQL:
    filter_labels: list[str] = strawberry.field(description="Allowed filter label keys.")
    group_labels: list[str] = strawberry.field(description="Allowed group-by label keys.")


@strawberry.type(
    name="QueryDefinitionMetricLabelEntry",
    description="Added in 26.3.0. Key-value label entry from Prometheus result.",
)
class MetricLabelEntryGQL:
    key: str
    value: str

    @classmethod
    def from_metric_dict(cls, metric: dict[str, Any]) -> list[Self]:
        return [cls(key=k, value=str(v)) for k, v in metric.items()]


@strawberry.type(
    name="QueryDefinitionMetricResultValue",
    description="Added in 26.3.0. Single timestamp-value pair from Prometheus.",
)
class MetricResultValueGQL:
    timestamp: float
    value: str


@strawberry.type(
    name="QueryDefinitionMetricResult",
    description="Added in 26.3.0. Single metric result from Prometheus query.",
)
class MetricResultGQL:
    metric: list[MetricLabelEntryGQL] = strawberry.field(
        description="Metric labels as key-value entries."
    )
    values: list[MetricResultValueGQL] = strawberry.field(description="Time-series values.")

    @classmethod
    def from_metric_response(cls, metric_response: MetricResponse) -> Self:
        return cls(
            metric=MetricLabelEntryGQL.from_metric_dict(
                metric_response.metric.model_dump(exclude_none=True)
            ),
            values=[
                MetricResultValueGQL(timestamp=ts, value=val) for ts, val in metric_response.values
            ],
        )


@strawberry.type(
    name="QueryDefinitionExecuteResult",
    description="Added in 26.3.0. Result from executing a query definition.",
)
class QueryDefinitionResultGQL:
    status: str = strawberry.field(description="Prometheus response status.")
    result_type: str = strawberry.field(description="Result type (e.g., matrix).")
    result: list[MetricResultGQL] = strawberry.field(description="Metric result entries.")


@strawberry.type(
    name="DeleteQueryDefinitionPayload",
    description="Added in 26.3.0. Payload returned after deleting a query definition.",
)
class DeleteQueryDefinitionPayload:
    id: ID = strawberry.field(description="ID of the deleted query definition.")
