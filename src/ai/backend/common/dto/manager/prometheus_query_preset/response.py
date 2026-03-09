"""
Response DTOs for Prometheus Query Definition API endpoints.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "CreateQueryDefinitionResponse",
    "DeleteQueryDefinitionResponse",
    "ExecuteQueryDefinitionResponse",
    "GetQueryDefinitionResponse",
    "MetricLabelEntryDTO",
    "MetricValueDTO",
    "ModifyQueryDefinitionResponse",
    "PaginationInfo",
    "QueryDefinitionDTO",
    "QueryDefinitionExecuteData",
    "QueryDefinitionMetricResult",
    "QueryDefinitionOptionsDTO",
    "SearchQueryDefinitionsResponse",
)


class QueryDefinitionOptionsDTO(BaseModel):
    """Options DTO for a prometheus query definition."""

    filter_labels: list[str] = Field(description="Allowed filter label keys")
    group_labels: list[str] = Field(description="Allowed group-by label keys")


class QueryDefinitionDTO(BaseModel):
    """DTO for prometheus query definition data."""

    id: UUID = Field(description="Query definition ID")
    name: str = Field(description="Human-readable name")
    metric_name: str = Field(description="Prometheus metric name")
    query_template: str = Field(description="PromQL template")
    time_window: str | None = Field(default=None, description="Default time window")
    options: QueryDefinitionOptionsDTO = Field(description="Query definition options")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class PaginationInfo(BaseModel):
    """Pagination information."""

    total: int = Field(description="Total count of items")
    offset: int = Field(description="Current offset")
    limit: int = Field(description="Current limit")


class CreateQueryDefinitionResponse(BaseResponseModel):
    """Response for creating a query definition."""

    item: QueryDefinitionDTO


class GetQueryDefinitionResponse(BaseResponseModel):
    """Response for getting a query definition by ID."""

    item: QueryDefinitionDTO


class SearchQueryDefinitionsResponse(BaseResponseModel):
    """Response for searching query definitions."""

    items: list[QueryDefinitionDTO]
    pagination: PaginationInfo


class ModifyQueryDefinitionResponse(BaseResponseModel):
    """Response for modifying a query definition."""

    item: QueryDefinitionDTO


class DeleteQueryDefinitionResponse(BaseResponseModel):
    """Response for deleting a query definition."""

    id: UUID = Field(description="Deleted query definition ID")


class MetricLabelEntryDTO(BaseModel):
    """A key-value label entry in the execute response."""

    key: str
    value: str


class MetricValueDTO(BaseModel):
    """A single (timestamp, value) data point from Prometheus."""

    timestamp: float
    value: str


class QueryDefinitionMetricResult(BaseModel):
    """A single metric result from query definition execution."""

    metric: list[MetricLabelEntryDTO]
    values: list[MetricValueDTO]


class QueryDefinitionExecuteData(BaseModel):
    """Data field of the execute response."""

    result_type: str
    result: list[QueryDefinitionMetricResult]


class ExecuteQueryDefinitionResponse(BaseResponseModel):
    """Response for executing a query definition."""

    status: str
    data: QueryDefinitionExecuteData
