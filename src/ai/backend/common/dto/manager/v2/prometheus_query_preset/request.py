"""
Request DTOs for prometheus_query_preset DTO v2.
"""

from __future__ import annotations

import re
from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.dto.clients.prometheus.defs import PROMETHEUS_DURATION_PATTERN
from ai.backend.common.dto.clients.prometheus.request import QueryTimeRange
from ai.backend.common.dto.manager.query import StringFilter

from .types import OrderDirection, QueryDefinitionOrderField

__all__ = (
    # Options inputs
    "CreateQueryDefinitionOptionsInput",
    "ModifyQueryDefinitionOptionsInput",
    "ExecuteQueryDefinitionOptionsInput",
    # CRUD inputs
    "CreateQueryDefinitionInput",
    "ModifyQueryDefinitionInput",
    "DeleteQueryDefinitionInput",
    # Search
    "QueryDefinitionFilter",
    "QueryDefinitionOrder",
    "SearchQueryDefinitionsInput",
    # Execute supporting
    "MetricLabelEntry",
    "ExecuteQueryDefinitionInput",
    # Query time range
    "QueryTimeRangeInputDTO",
)

_DEFAULT_PAGE_LIMIT = 50


class QueryTimeRangeInputDTO(BaseRequestModel):
    """Input for a Prometheus query time range."""

    start: datetime = Field(description="Start of the time range.")
    end: datetime = Field(description="End of the time range.")
    step: str = Field(description="Query resolution step (e.g., '60s').")


class CreateQueryDefinitionOptionsInput(BaseRequestModel):
    """Options for a new prometheus query definition."""

    filter_labels: list[str] = Field(description="Allowed filter label keys")
    group_labels: list[str] = Field(description="Allowed group-by label keys")


class CreateQueryDefinitionInput(BaseRequestModel):
    """Input for creating a prometheus query definition."""

    name: str = Field(min_length=1, max_length=256, description="Human-readable name")
    metric_name: str = Field(description="Prometheus metric name")
    query_template: str = Field(description="PromQL template with placeholders")
    time_window: str | None = Field(
        default=None,
        pattern=PROMETHEUS_DURATION_PATTERN,
        description="Default time window (e.g. '5m', '1h')",
    )
    options: CreateQueryDefinitionOptionsInput = Field(description="Query definition options")

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be blank or whitespace-only")
        return stripped


class ModifyQueryDefinitionOptionsInput(BaseRequestModel):
    """Options for modifying a prometheus query definition.

    Each field is optional — only provided fields are updated.
    """

    filter_labels: list[str] | None = Field(default=None, description="Allowed filter label keys")
    group_labels: list[str] | None = Field(default=None, description="Allowed group-by label keys")


class ModifyQueryDefinitionInput(BaseRequestModel):
    """Input for modifying a prometheus query definition.

    Only ``time_window`` uses ``Sentinel`` because it is the only nullable DB column;
    all other fields are non-nullable, so ``None`` simply means "do not update".
    """

    name: str | None = Field(default=None, description="Updated human-readable name")
    metric_name: str | None = Field(default=None, description="Updated Prometheus metric name")
    query_template: str | None = Field(
        default=None, description="Updated PromQL template with placeholders"
    )
    time_window: str | Sentinel | None = Field(
        default=SENTINEL,
        description=(
            "Updated default time window. "
            "Pass SENTINEL (default) to leave unchanged; pass None to clear."
        ),
    )
    options: ModifyQueryDefinitionOptionsInput | None = Field(
        default=None, description="Updated query definition options"
    )

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str | None) -> str | None:
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be blank or whitespace-only")
        return stripped

    @field_validator("time_window", mode="after")
    @classmethod
    def _validate_time_window(cls, v: str | Sentinel | None) -> str | Sentinel | None:
        if isinstance(v, str) and not re.match(PROMETHEUS_DURATION_PATTERN, v):
            raise ValueError(f"Invalid Prometheus duration format: {v!r}")
        return v


class DeleteQueryDefinitionInput(BaseRequestModel):
    """Input for deleting a prometheus query definition."""

    id: UUID = Field(description="Query definition ID to delete")


class QueryDefinitionFilter(BaseRequestModel):
    """Filter for prometheus query definition search."""

    name: StringFilter | None = Field(default=None, description="Filter by name")


class QueryDefinitionOrder(BaseRequestModel):
    """Order specification for prometheus query definitions."""

    field: QueryDefinitionOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


class SearchQueryDefinitionsInput(BaseRequestModel):
    """Input for searching prometheus query definitions with filters, orders, and pagination."""

    filter: QueryDefinitionFilter | None = Field(default=None, description="Filter conditions")
    order: list[QueryDefinitionOrder] | None = Field(
        default=None, description="Order specifications"
    )
    limit: int = Field(
        default=_DEFAULT_PAGE_LIMIT, ge=1, le=1000, description="Maximum items to return"
    )
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class MetricLabelEntry(BaseRequestModel):
    """A key-value label entry for executing a query definition."""

    key: str = Field(description="Label key")
    value: str = Field(description="Label value")


class ExecuteQueryDefinitionOptionsInput(BaseRequestModel):
    """Execution options for a prometheus query definition."""

    filter_labels: list[MetricLabelEntry] = Field(
        default_factory=list,
        description="Filter labels as key-value pairs",
    )
    group_labels: list[str] = Field(
        default_factory=list,
        description="Group-by labels",
    )


class ExecuteQueryDefinitionInput(BaseRequestModel):
    """Input for executing a prometheus query definition."""

    options: ExecuteQueryDefinitionOptionsInput = Field(
        default_factory=ExecuteQueryDefinitionOptionsInput,
        description="Execution options (filter and group labels)",
    )
    time_window: str | None = Field(
        default=None,
        pattern=PROMETHEUS_DURATION_PATTERN,
        description="Time window override (e.g. '5m', '1h')",
    )
    time_range: QueryTimeRange | None = Field(
        default=None,
        description=(
            "Time range for the query; if omitted, executes an instant query at the current time"
        ),
    )
