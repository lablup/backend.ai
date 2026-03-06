"""
Request DTOs for Prometheus Query Preset API endpoints.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

import re

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.dto.clients.prometheus.defs import PROMETHEUS_DURATION_PATTERN
from ai.backend.common.dto.clients.prometheus.request import QueryTimeRange
from ai.backend.common.dto.manager.defs import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT

__all__ = (
    "CreatePresetRequest",
    "ExecutePresetOptionsRequest",
    "ExecutePresetRequest",
    "MetricLabelEntry",
    "ModifyCreatePresetOptionsRequest",
    "ModifyPresetRequest",
    "CreatePresetOptionsRequest",
    "SearchPresetsRequest",
)


class CreatePresetOptionsRequest(BaseRequestModel):
    """Options for a prometheus query preset."""

    filter_labels: list[str] = Field(description="Allowed filter label keys")
    group_labels: list[str] = Field(description="Allowed group-by label keys")


class CreatePresetRequest(BaseRequestModel):
    """Request to create a prometheus query preset."""

    name: str = Field(description="Human-readable preset name")
    metric_name: str = Field(description="Prometheus metric name")
    query_template: str = Field(description="PromQL template with placeholders")
    time_window: str | None = Field(
        default=None, pattern=PROMETHEUS_DURATION_PATTERN, description="Default time window"
    )
    options: CreatePresetOptionsRequest = Field(description="Preset options")


class ModifyCreatePresetOptionsRequest(BaseRequestModel):
    """Options for modifying a prometheus query preset.

    Each field is optional — only provided fields are updated.
    """

    filter_labels: list[str] | None = Field(default=None, description="Allowed filter label keys")
    group_labels: list[str] | None = Field(default=None, description="Allowed group-by label keys")


class ModifyPresetRequest(BaseRequestModel):
    """Request to modify a prometheus query preset.

    Only ``time_window`` uses ``Sentinel`` because it is the only nullable DB column;
    all other fields are non-nullable, so ``None`` simply means "do not update".
    """

    name: str | None = Field(default=None, description="Human-readable preset name")
    metric_name: str | None = Field(default=None, description="Prometheus metric name")
    query_template: str | None = Field(
        default=None, description="PromQL template with placeholders"
    )
    time_window: str | Sentinel | None = Field(default=SENTINEL, description="Default time window")
    options: ModifyCreatePresetOptionsRequest | None = Field(
        default=None, description="Preset options"
    )

    @field_validator("time_window", mode="after")
    @classmethod
    def _validate_time_window(cls, v: str | Sentinel | None) -> str | Sentinel | None:
        if isinstance(v, str) and not re.match(PROMETHEUS_DURATION_PATTERN, v):
            raise ValueError(f"Invalid Prometheus duration format: {v!r}")
        return v


class SearchPresetsRequest(BaseRequestModel):
    """Request to search prometheus query presets."""

    offset: int = Field(default=0, ge=0, description="Pagination offset")
    limit: int = Field(
        default=DEFAULT_PAGE_LIMIT,
        ge=1,
        le=MAX_PAGE_LIMIT,
        description="Pagination limit",
    )


class MetricLabelEntry(BaseRequestModel):
    """A key-value label entry for executing a preset."""

    key: str = Field(description="Label key")
    value: str = Field(description="Label value")


class ExecutePresetOptionsRequest(BaseRequestModel):
    """Execution options for a prometheus query preset."""

    filter_labels: list[MetricLabelEntry] = Field(
        default_factory=list,
        description="Filter labels as key-value pairs",
    )
    group_labels: list[str] = Field(
        default_factory=list,
        description="Group-by labels",
    )


class ExecutePresetRequest(BaseRequestModel):
    """Request to execute a prometheus query preset."""

    options: ExecutePresetOptionsRequest = Field(
        default_factory=ExecutePresetOptionsRequest,
        description="Execution options (filter and group labels)",
    )
    window: str | None = Field(
        default=None, pattern=PROMETHEUS_DURATION_PATTERN, description="Time window override"
    )
    time_range: QueryTimeRange | None = Field(
        default=None,
        description="Time range for the query; if omitted, executes an instant query at the current time",
    )
