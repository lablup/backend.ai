"""Prometheus query preset GQL payload and result types."""

from __future__ import annotations

from uuid import UUID

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
    gql_field,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin


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
    pass


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Single timestamp-value pair from Prometheus.",
    ),
    model=MetricValueInfo,
    all_fields=True,
    name="QueryDefinitionMetricResultValue",
)
class MetricResultValueGQL(PydanticOutputMixin[MetricValueInfo]):
    pass


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Single metric result from Prometheus query.",
    ),
    model=QueryDefinitionMetricResultInfo,
    name="QueryDefinitionMetricResult",
)
class MetricResultGQL(PydanticOutputMixin[QueryDefinitionMetricResultInfo]):
    metric: list[MetricLabelEntryGQL] = gql_field(description="Metric labels as key-value entries.")
    values: list[MetricResultValueGQL] = gql_field(description="Time-series values.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Result from executing a query definition.",
    ),
    model=QueryDefinitionResultInfoDTO,
    name="QueryDefinitionExecuteResult",
)
class QueryDefinitionResultGQL(PydanticOutputMixin[QueryDefinitionResultInfoDTO]):
    status: str = gql_field(description="Prometheus response status.")
    result_type: str = gql_field(description="Result type (e.g., matrix).")
    result: list[MetricResultGQL] = gql_field(description="Metric result entries.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Payload returned after deleting a query definition.",
    ),
    model=DeleteQueryDefinitionPayloadDTO,
    name="DeleteQueryDefinitionPayload",
)
class DeleteQueryDefinitionPayload(PydanticOutputMixin[DeleteQueryDefinitionPayloadDTO]):
    id: UUID = gql_field(description="Deleted query definition ID.")
