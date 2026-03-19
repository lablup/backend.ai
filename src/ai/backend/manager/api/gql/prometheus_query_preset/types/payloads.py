"""Prometheus query preset GQL payload and result types."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

import strawberry

from ai.backend.common.dto.manager.v2.prometheus_query_preset.response import (
    DeleteQueryDefinitionPayload as DeleteQueryDefinitionPayloadDTO,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.response import (
    QueryDefinitionResultInfo as QueryDefinitionResultInfoDTO,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.types import (
    MetricLabelEntryInfo,
    MetricValueInfo,
    QueryDefinitionOptionsInfo,
)

if TYPE_CHECKING:
    from ai.backend.common.dto.clients.prometheus.response import MetricResponse


@strawberry.experimental.pydantic.type(
    model=QueryDefinitionOptionsInfo,
    name="QueryDefinitionOptions",
    description="Added in 26.3.0. Options for query definition label governance.",
    all_fields=True,
)
class QueryDefinitionOptionsGQL:
    pass


@strawberry.experimental.pydantic.type(
    model=MetricLabelEntryInfo,
    name="QueryDefinitionMetricLabelEntry",
    description="Added in 26.3.0. Key-value label entry from Prometheus result.",
    all_fields=True,
)
class MetricLabelEntryGQL:
    @classmethod
    def from_metric_dict(cls, metric: dict[str, Any]) -> list[MetricLabelEntryGQL]:
        return [
            cls.from_pydantic(MetricLabelEntryInfo(key=k, value=str(v))) for k, v in metric.items()
        ]


@strawberry.experimental.pydantic.type(
    model=MetricValueInfo,
    name="QueryDefinitionMetricResultValue",
    description="Added in 26.3.0. Single timestamp-value pair from Prometheus.",
    all_fields=True,
)
class MetricResultValueGQL:
    pass


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
                MetricResultValueGQL.from_pydantic(MetricValueInfo(timestamp=ts, value=val))
                for ts, val in metric_response.values
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

    @classmethod
    def from_pydantic(cls, dto: QueryDefinitionResultInfoDTO) -> Self:
        return cls(
            status=dto.status,
            result_type=dto.result_type,
            result=[
                MetricResultGQL(
                    metric=[MetricLabelEntryGQL.from_pydantic(entry) for entry in item.metric],
                    values=[MetricResultValueGQL.from_pydantic(v) for v in item.values],
                )
                for item in dto.result
            ],
        )


@strawberry.experimental.pydantic.type(
    model=DeleteQueryDefinitionPayloadDTO,
    name="DeleteQueryDefinitionPayload",
    description="Added in 26.3.0. Payload returned after deleting a query definition.",
    all_fields=True,
)
class DeleteQueryDefinitionPayload:
    """Payload for query definition deletion mutation."""
