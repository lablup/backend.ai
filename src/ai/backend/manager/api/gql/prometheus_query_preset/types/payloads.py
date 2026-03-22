"""Prometheus query preset GQL payload and result types."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

import strawberry
from strawberry import ID

from ai.backend.common.dto.manager.v2.prometheus_query_preset.response import (
    DeleteQueryDefinitionPayload as DeleteQueryDefinitionPayloadDTO,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.response import (
    QueryDefinitionMetricResultInfo,
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
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin

if TYPE_CHECKING:
    from ai.backend.common.dto.clients.prometheus.response import MetricResponse


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Options for query definition label governance.",
    ),
    model=QueryDefinitionOptionsInfo,
    all_fields=True,
    name="QueryDefinitionOptions",
)
class QueryDefinitionOptionsGQL(PydanticOutputMixin[QueryDefinitionOptionsInfo]):
    pass


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Key-value label entry from Prometheus result.",
    ),
    model=MetricLabelEntryInfo,
    all_fields=True,
    name="MetricLabelEntry",
)
class MetricLabelEntryGQL(PydanticOutputMixin[MetricLabelEntryInfo]):
    @classmethod
    def from_metric_dict(cls, data: dict[str, str]) -> list[Self]:
        return [cls.from_pydantic(MetricLabelEntryInfo(key=k, value=v)) for k, v in data.items()]


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Single timestamp-value pair from Prometheus.",
    ),
    model=MetricValueInfo,
    all_fields=True,
    name="MetricResultValue",
)
class MetricResultValueGQL(PydanticOutputMixin[MetricValueInfo]):
    pass


@gql_from_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Single metric result from Prometheus query.",
    ),
    name="QueryDefinitionMetricResult",
)
class MetricResultGQL(PydanticOutputMixin[QueryDefinitionMetricResultInfo]):
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


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Payload returned after deleting a query definition.",
    ),
    model=DeleteQueryDefinitionPayloadDTO,
    fields=["id"],
    name="DeleteQueryDefinitionPayload",
)
class DeleteQueryDefinitionPayload(PydanticOutputMixin[DeleteQueryDefinitionPayloadDTO]):
    id: ID = strawberry.field(description="Deleted query definition ID.")
