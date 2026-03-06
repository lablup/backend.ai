"""
Request DTOs for Prometheus Query Definition API endpoints.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

import re

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.dto.clients.prometheus.defs import PROMETHEUS_DURATION_PATTERN
from ai.backend.common.dto.clients.prometheus.request import QueryTimeRange
from ai.backend.common.dto.manager.defs import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT
from ai.backend.common.dto.manager.query import StringFilter

from .types import QueryDefinitionOrder

__all__ = (
    "CreateQueryDefinitionOptionsRequest",
    "CreateQueryDefinitionRequest",
    "ExecuteQueryDefinitionOptionsRequest",
    "ExecuteQueryDefinitionRequest",
    "MetricLabelEntry",
    "ModifyQueryDefinitionOptionsRequest",
    "ModifyQueryDefinitionRequest",
    "QueryDefinitionFilter",
    "SearchQueryDefinitionsRequest",
)


class CreateQueryDefinitionOptionsRequest(BaseRequestModel):
    """Options for a prometheus query definition."""

    filter_labels: list[str] = Field(description="Allowed filter label keys")
    group_labels: list[str] = Field(description="Allowed group-by label keys")


class CreateQueryDefinitionRequest(BaseRequestModel):
    """Request to create a prometheus query definition."""

    name: str = Field(description="Human-readable name")
    metric_name: str = Field(description="Prometheus metric name")
    query_template: str = Field(description="PromQL template with placeholders")
    time_window: str | None = Field(
        default=None, pattern=PROMETHEUS_DURATION_PATTERN, description="Default time window"
    )
    options: CreateQueryDefinitionOptionsRequest = Field(description="Query definition options")


class ModifyQueryDefinitionOptionsRequest(BaseRequestModel):
    """Options for modifying a prometheus query definition.

    Each field is optional — only provided fields are updated.
    """

    filter_labels: list[str] | None = Field(default=None, description="Allowed filter label keys")
    group_labels: list[str] | None = Field(default=None, description="Allowed group-by label keys")


class ModifyQueryDefinitionRequest(BaseRequestModel):
    """Request to modify a prometheus query definition.

    Only ``time_window`` uses ``Sentinel`` because it is the only nullable DB column;
    all other fields are non-nullable, so ``None`` simply means "do not update".
    """

    name: str | None = Field(default=None, description="Human-readable name")
    metric_name: str | None = Field(default=None, description="Prometheus metric name")
    query_template: str | None = Field(
        default=None, description="PromQL template with placeholders"
    )
    time_window: str | Sentinel | None = Field(default=SENTINEL, description="Default time window")
    options: ModifyQueryDefinitionOptionsRequest | None = Field(
        default=None, description="Query definition options"
    )

    @field_validator("time_window", mode="after")
    @classmethod
    def _validate_time_window(cls, v: str | Sentinel | None) -> str | Sentinel | None:
        if isinstance(v, str) and not re.match(PROMETHEUS_DURATION_PATTERN, v):
            raise ValueError(f"Invalid Prometheus duration format: {v!r}")
        return v


class QueryDefinitionFilter(BaseRequestModel):
    """Filter for prometheus query definition search."""

    name: StringFilter | None = Field(default=None, description="Filter by name")
    metric_name: StringFilter | None = Field(default=None, description="Filter by metric name")


class SearchQueryDefinitionsRequest(BaseRequestModel):
    """Request body for searching prometheus query definitions with filters, orders, and pagination."""

    filter: QueryDefinitionFilter | None = Field(default=None, description="Filter conditions")
    order: list[QueryDefinitionOrder] | None = Field(
        default=None, description="Order specifications"
    )
    offset: int = Field(default=0, ge=0, description="Number of items to skip")
    limit: int = Field(
        default=DEFAULT_PAGE_LIMIT,
        ge=1,
        le=MAX_PAGE_LIMIT,
        description="Maximum items to return",
    )


class MetricLabelEntry(BaseRequestModel):
    """A key-value label entry for executing a query definition."""

    key: str = Field(description="Label key")
    value: str = Field(description="Label value")


class ExecuteQueryDefinitionOptionsRequest(BaseRequestModel):
    """Execution options for a prometheus query definition."""

    filter_labels: list[MetricLabelEntry] = Field(
        default_factory=list,
        description="Filter labels as key-value pairs",
    )
    group_labels: list[str] = Field(
        default_factory=list,
        description="Group-by labels",
    )


class ExecuteQueryDefinitionRequest(BaseRequestModel):
    """Request to execute a prometheus query definition."""

    options: ExecuteQueryDefinitionOptionsRequest = Field(
        default_factory=ExecuteQueryDefinitionOptionsRequest,
        description="Execution options (filter and group labels)",
    )
    window: str | None = Field(
        default=None, pattern=PROMETHEUS_DURATION_PATTERN, description="Time window override"
    )
    time_range: QueryTimeRange | None = Field(
        default=None,
        description="Time range for the query; if omitted, executes an instant query at the current time",
    )
