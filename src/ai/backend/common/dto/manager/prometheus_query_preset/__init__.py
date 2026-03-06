"""
Prometheus Query Preset DTOs for Manager API.
"""

from .path import (
    PresetIdPathParam,
)
from .request import (
    CreatePresetOptionsRequest,
    CreatePresetRequest,
    ExecutePresetOptionsRequest,
    ExecutePresetRequest,
    MetricLabelEntry,
    ModifyCreatePresetOptionsRequest,
    ModifyPresetRequest,
    SearchPresetsRequest,
)
from .response import (
    CreatePresetResponse,
    DeletePresetResponse,
    ExecutePresetResponse,
    GetPresetResponse,
    MetricLabelEntryDTO,
    MetricValueDTO,
    ModifyPresetResponse,
    PaginationInfo,
    PresetDTO,
    PresetExecuteData,
    PresetMetricResult,
    PresetOptionsDTO,
    SearchPresetsResponse,
)

__all__ = (
    # Path DTOs
    "PresetIdPathParam",
    # Request DTOs
    "CreatePresetRequest",
    "ExecutePresetOptionsRequest",
    "ExecutePresetRequest",
    "MetricLabelEntry",
    "ModifyCreatePresetOptionsRequest",
    "ModifyPresetRequest",
    "CreatePresetOptionsRequest",
    "SearchPresetsRequest",
    # Response DTOs
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
