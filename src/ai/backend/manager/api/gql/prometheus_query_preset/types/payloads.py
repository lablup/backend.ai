"""Prometheus query preset GQL payload and result types."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

import strawberry
from strawberry import ID

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
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_from_pydantic_type,
    gql_output_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin

if TYPE_CHECKING:
    from ai.backend.common.dto.clients.prometheus.response import MetricResponse


@gql_from_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Options for query definition label governance.",
    ),
    name="QueryDefinitionOptions",
)
class QueryDefinitionOptionsGQL(PydanticOutputMixin[QueryDefinitionOptionsInfo]):
    filter_labels: list[str] = strawberry.field(description="Allowed filter label keys.")
    group_labels: list[str] = strawberry.field(description="Allowed group-by label keys.")


@gql_from_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Key-value label entry from Prometheus result.",
    ),
    name="QueryDefinitionMetricLabelEntry",
)
class MetricLabelEntryGQL(PydanticOutputMixin[MetricLabelEntryInfo]):
    key: str = strawberry.field(description="Label key.")
    value: str = strawberry.field(description="Label value.")

    @classmethod
    def from_metric_dict(cls, metric: dict[str, Any]) -> list[MetricLabelEntryGQL]:
        return [cls(key=k, value=str(v)) for k, v in metric.items()]


@gql_from_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Single timestamp-value pair from Prometheus.",
    ),
    name="QueryDefinitionMetricResultValue",
)
class MetricResultValueGQL(PydanticOutputMixin[MetricValueInfo]):
    timestamp: float = strawberry.field(description="Unix timestamp of the data point.")
    value: str = strawberry.field(description="Metric value as a string to preserve precision.")


@gql_output_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Single metric result from Prometheus query.",
    ),
    name="QueryDefinitionMetricResult",
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


@gql_from_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Result from executing a query definition.",
    ),
    name="QueryDefinitionExecuteResult",
)
class QueryDefinitionResultGQL(PydanticOutputMixin[QueryDefinitionResultInfoDTO]):
    status: str = strawberry.field(description="Prometheus response status.")
    result_type: str = strawberry.field(description="Result type (e.g., matrix).")
    result: list[MetricResultGQL] = strawberry.field(description="Metric result entries.")

    @classmethod
    def from_pydantic(cls, dto: QueryDefinitionResultInfoDTO) -> Self:  # type: ignore[override]
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


@gql_from_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Payload returned after deleting a query definition.",
    ),
    name="DeleteQueryDefinitionPayload",
)
class DeleteQueryDefinitionPayload(PydanticOutputMixin[DeleteQueryDefinitionPayloadDTO]):
    """Payload for query definition deletion mutation."""

    id: ID = strawberry.field(description="Deleted query definition ID.")

    @classmethod
    def from_pydantic(cls, dto: DeleteQueryDefinitionPayloadDTO) -> Self:  # type: ignore[override]
        return cls(id=ID(str(dto.id)))
