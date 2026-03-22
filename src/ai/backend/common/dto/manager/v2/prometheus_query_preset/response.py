"""
Response DTOs for prometheus_query_preset DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

from .types import MetricLabelEntryInfo, MetricValueInfo, QueryDefinitionOptionsInfo

__all__ = (
    # Node
    "QueryDefinitionNode",
    # CRUD payloads
    "CreateQueryDefinitionPayload",
    "ModifyQueryDefinitionPayload",
    "DeleteQueryDefinitionPayload",
    "GetQueryDefinitionPayload",
    # Search payloads
    "AdminSearchQueryDefinitionsPayload",
    "SearchQueryDefinitionsPayload",
    # Execute payloads
    "QueryDefinitionMetricResultInfo",
    "QueryDefinitionExecuteDataInfo",
    "ExecuteQueryDefinitionPayload",
    # GQL-layer sub-models
    "QueryDefinitionResultInfo",
    "CreateQueryDefinitionGQLPayload",
    "ModifyQueryDefinitionGQLPayload",
)


class QueryDefinitionNode(BaseResponseModel):
    """Node representing a single prometheus query definition."""

    id: UUID = Field(description="Query definition ID")
    name: str = Field(description="Human-readable name")
    metric_name: str = Field(description="Prometheus metric name")
    query_template: str = Field(description="PromQL template with placeholders")
    time_window: str | None = Field(default=None, description="Default time window")
    options: QueryDefinitionOptionsInfo = Field(description="Query definition options")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class CreateQueryDefinitionPayload(BaseResponseModel):
    """Payload for creating a query definition."""

    item: QueryDefinitionNode = Field(description="Created query definition")


class ModifyQueryDefinitionPayload(BaseResponseModel):
    """Payload for modifying a query definition."""

    item: QueryDefinitionNode = Field(description="Updated query definition")


class DeleteQueryDefinitionPayload(BaseResponseModel):
    """Payload for deleting a query definition."""

    id: UUID = Field(description="Deleted query definition ID")


class GetQueryDefinitionPayload(BaseResponseModel):
    """Payload for getting a single query definition."""

    item: QueryDefinitionNode | None = Field(default=None, description="Query definition data")


class AdminSearchQueryDefinitionsPayload(BaseResponseModel):
    """Payload for admin-scoped paginated query definition search results."""

    items: list[QueryDefinitionNode] = Field(description="List of query definition nodes.")
    total_count: int = Field(description="Total number of query definitions matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")


class SearchQueryDefinitionsPayload(BaseResponseModel):
    """Payload for searching query definitions."""

    items: list[QueryDefinitionNode] = Field(description="List of query definitions")
    total_count: int = Field(description="Total count of matching records")


class QueryDefinitionMetricResultInfo(BaseResponseModel):
    """A single metric result from query definition execution."""

    metric: list[MetricLabelEntryInfo] = Field(description="Label key-value pairs for this series")
    values: list[MetricValueInfo] = Field(
        description="Data points (timestamp, value) for this series"
    )


class QueryDefinitionExecuteDataInfo(BaseResponseModel):
    """Data field of the execute response."""

    result_type: str = Field(description="Prometheus result type (e.g. 'matrix', 'vector')")
    result: list[QueryDefinitionMetricResultInfo] = Field(description="List of metric results")


class ExecuteQueryDefinitionPayload(BaseResponseModel):
    """Payload for executing a query definition."""

    status: str = Field(description="Prometheus query status (e.g. 'success')")
    data: QueryDefinitionExecuteDataInfo = Field(description="Query execution data")


class QueryDefinitionResultInfo(BaseResponseModel):
    """GQL-layer result DTO for executing a query definition."""

    status: str = Field(description="Prometheus response status.")
    result_type: str = Field(description="Result type (e.g., matrix).")
    result: list[QueryDefinitionMetricResultInfo] = Field(description="Metric result entries.")


class CreateQueryDefinitionGQLPayload(BaseResponseModel):
    """GQL-layer payload returned after creating a query definition."""

    preset: QueryDefinitionNode = Field(description="Created query definition.")


class ModifyQueryDefinitionGQLPayload(BaseResponseModel):
    """GQL-layer payload returned after modifying a query definition."""

    preset: QueryDefinitionNode = Field(description="Updated query definition.")
