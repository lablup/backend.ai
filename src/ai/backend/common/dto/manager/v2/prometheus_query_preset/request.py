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
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter

from .types import OrderDirection, QueryDefinitionOrderField
from .validators import validate_query_template

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
    # Preview
    "PreviewQueryDefinitionInput",
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
    description: str | None = Field(default=None, description="Human-readable description")
    rank: int = Field(default=0, ge=0, description="Sort rank (lower = higher priority)")
    category_id: UUID | None = Field(default=None, description="Category ID")
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

    @field_validator("query_template")
    @classmethod
    def _validate_query_template(cls, v: str) -> str:
        validate_query_template(v)
        return v


class ModifyQueryDefinitionOptionsInput(BaseRequestModel):
    """Options for modifying a prometheus query definition.

    Each field is optional — only provided fields are updated.
    """

    filter_labels: list[str] | None = Field(default=None, description="Allowed filter label keys")
    group_labels: list[str] | None = Field(default=None, description="Allowed group-by label keys")


class ModifyQueryDefinitionInput(BaseRequestModel):
    """Input for modifying a prometheus query definition.

    Nullable DB columns (``time_window``, ``description``, ``category_id``) use the
    ``Sentinel`` pattern so callers can distinguish "leave unchanged" from "clear to null".
    Non-nullable fields use ``None`` to mean "do not update".
    """

    name: str | None = Field(default=None, description="Updated human-readable name")
    description: str | Sentinel | None = Field(
        default=SENTINEL,
        description=(
            "Updated description. Pass SENTINEL (default) to leave unchanged; pass None to clear."
        ),
    )
    rank: int | None = Field(default=None, ge=0, description="Updated sort rank")
    category_id: UUID | Sentinel | None = Field(
        default=SENTINEL,
        description=(
            "Updated category ID. Pass SENTINEL (default) to leave unchanged; pass None to clear."
        ),
    )
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

    @field_validator("query_template")
    @classmethod
    def _validate_query_template(cls, v: str | None) -> str | None:
        if v is not None:
            validate_query_template(v)
        return v


class DeleteQueryDefinitionInput(BaseRequestModel):
    """Input for deleting a prometheus query definition."""

    id: UUID = Field(description="Query definition ID to delete")


class QueryDefinitionFilter(BaseRequestModel):
    """Filter for prometheus query definition search."""

    name: StringFilter | None = Field(default=None, description="Filter by name")
    category_id: UUIDFilter | None = Field(default=None, description="Filter by category ID")
    AND: list[QueryDefinitionFilter] | None = Field(
        default=None, description="AND logical combinator."
    )
    OR: list[QueryDefinitionFilter] | None = Field(
        default=None, description="OR logical combinator."
    )
    NOT: list[QueryDefinitionFilter] | None = Field(
        default=None, description="NOT logical combinator."
    )


QueryDefinitionFilter.model_rebuild()


class QueryDefinitionOrder(BaseRequestModel):
    """Order specification for prometheus query definitions."""

    field: QueryDefinitionOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


class SearchQueryDefinitionsInput(BaseRequestModel):
    """Input for searching prometheus query definitions with filters, orders, and pagination.

    Supports two pagination modes (mutually exclusive):
    - Cursor-based: first/after (forward) or last/before (backward)
    - Offset-based: limit/offset
    """

    filter: QueryDefinitionFilter | None = Field(default=None, description="Filter conditions")
    order: list[QueryDefinitionOrder] | None = Field(
        default=None, description="Order specifications"
    )
    # Cursor-based pagination (Relay)
    first: int | None = Field(default=None, ge=1, description="Number of items from the start.")
    after: str | None = Field(default=None, description="Cursor to paginate forward from.")
    last: int | None = Field(default=None, ge=1, description="Number of items from the end.")
    before: str | None = Field(default=None, description="Cursor to paginate backward from.")
    # Offset-based pagination
    limit: int | None = Field(default=None, ge=1, le=1000, description="Maximum items to return")
    offset: int | None = Field(default=None, ge=0, description="Number of items to skip")


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


class PreviewQueryDefinitionInput(BaseRequestModel):
    """Input for previewing a prometheus query template before saving (admin only)."""

    query_template: str = Field(description="PromQL template to validate")

    @field_validator("query_template")
    @classmethod
    def _validate_query_template(cls, v: str) -> str:
        validate_query_template(v)
        return v


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
    time_range: QueryTimeRangeInputDTO | None = Field(
        default=None,
        description=(
            "Time range for the query; if omitted, executes an instant query at the current time"
        ),
    )
