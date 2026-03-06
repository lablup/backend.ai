"""
Response DTOs for Prometheus Query Preset API endpoints.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "CreatePresetResponse",
    "DeletePresetResponse",
    "ExecutePresetResponse",
    "GetPresetResponse",
    "MetricLabelEntryDTO",
    "MetricValueDTO",
    "ModifyPresetResponse",
    "PaginationInfo",
    "PresetDTO",
    "PresetExecuteData",
    "PresetMetricResult",
    "PresetOptionsDTO",
    "SearchPresetsResponse",
)


class PresetOptionsDTO(BaseModel):
    """Options DTO for a prometheus query preset."""

    filter_labels: list[str] = Field(description="Allowed filter label keys")
    group_labels: list[str] = Field(description="Allowed group-by label keys")


class PresetDTO(BaseModel):
    """DTO for prometheus query preset data."""

    id: UUID = Field(description="Preset ID")
    name: str = Field(description="Human-readable preset name")
    metric_name: str = Field(description="Prometheus metric name")
    query_template: str = Field(description="PromQL template")
    time_window: str | None = Field(default=None, description="Default time window")
    options: PresetOptionsDTO = Field(description="Preset options")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class PaginationInfo(BaseModel):
    """Pagination information."""

    total: int = Field(description="Total count of items")
    offset: int = Field(description="Current offset")
    limit: int = Field(description="Current limit")


class CreatePresetResponse(BaseResponseModel):
    """Response for creating a preset."""

    item: PresetDTO


class GetPresetResponse(BaseResponseModel):
    """Response for getting a preset by ID."""

    item: PresetDTO


class SearchPresetsResponse(BaseResponseModel):
    """Response for searching presets."""

    items: list[PresetDTO]
    pagination: PaginationInfo


class ModifyPresetResponse(BaseResponseModel):
    """Response for modifying a preset."""

    item: PresetDTO


class DeletePresetResponse(BaseResponseModel):
    """Response for deleting a preset."""

    id: UUID = Field(description="Deleted preset ID")


class MetricLabelEntryDTO(BaseModel):
    """A key-value label entry in the execute response."""

    key: str
    value: str


class MetricValueDTO(BaseModel):
    """A single (timestamp, value) data point from Prometheus."""

    timestamp: float
    value: str


class PresetMetricResult(BaseModel):
    """A single metric result from preset execution."""

    metric: list[MetricLabelEntryDTO]
    values: list[MetricValueDTO]


class PresetExecuteData(BaseModel):
    """Data field of the execute response."""

    result_type: str
    result: list[PresetMetricResult]


class ExecutePresetResponse(BaseResponseModel):
    """Response for executing a preset."""

    status: str
    data: PresetExecuteData
