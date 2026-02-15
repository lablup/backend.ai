"""
Response DTOs for Infrastructure REST API.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel, BaseRootResponseModel

__all__ = (
    # Nested DTOs
    "NumberFormatDTO",
    "AcceleratorMetadataDTO",
    "ScalingGroupDTO",
    "ResourcePresetDTO",
    # etcd responses
    "GetResourceSlotsResponse",
    "GetResourceMetadataResponse",
    "GetVFolderTypesResponse",
    "GetConfigResponse",
    "SetConfigResponse",
    "DeleteConfigResponse",
    # scaling_group responses
    "ListScalingGroupsResponse",
    "GetWSProxyVersionResponse",
    # resource responses
    "ListPresetsResponse",
    "CheckPresetsResponse",
    "RecalculateUsageResponse",
    "UsagePerMonthResponse",
    "UsagePerPeriodResponse",
    "MonthStatsResponse",
    "WatcherStatusResponse",
    "WatcherAgentActionResponse",
    "GetContainerRegistriesResponse",
)


# --- Nested DTOs ---


class NumberFormatDTO(BaseModel):
    """Number formatting configuration for resource slot display."""

    binary: bool = Field(description="Whether to use binary (base-2) formatting.")
    round_length: int = Field(description="Number of decimal places to round to.")


class AcceleratorMetadataDTO(BaseModel):
    """Metadata for an accelerator resource slot."""

    slot_name: str = Field(description="Internal slot name identifier.")
    description: str = Field(description="Human-readable description of the accelerator.")
    human_readable_name: str = Field(description="Short display name for the accelerator.")
    display_unit: str = Field(description="Unit label for display (e.g., 'Core', 'GiB', 'GPU').")
    number_format: NumberFormatDTO = Field(description="Number formatting configuration.")
    display_icon: str = Field(description="Icon identifier for UI rendering.")


class ScalingGroupDTO(BaseModel):
    """Minimal scaling group information."""

    name: str = Field(description="Name of the scaling group.")


class ResourcePresetDTO(BaseModel):
    """Resource preset configuration."""

    name: str = Field(description="Name of the resource preset.")
    resource_slots: dict[str, Any] = Field(description="Resource slot allocations.")
    shared_memory: str | None = Field(default=None, description="Shared memory size if configured.")


# --- etcd.py responses ---


class GetResourceSlotsResponse(BaseRootResponseModel[dict[str, str]]):
    """Response containing available resource slot types and their units.

    The handler returns a bare dict mapping resource slot names to their unit types.
    e.g., ``{"cpu": "count", "mem": "bytes", "cuda.device": "count"}``
    """


class GetResourceMetadataResponse(BaseRootResponseModel[dict[str, AcceleratorMetadataDTO]]):
    """Response containing metadata for accelerator resource slots.

    The handler returns a bare dict mapping slot names to their accelerator metadata.
    e.g., ``{"cpu": {"slot_name": "cpu", ...}, "cuda.device": {...}}``
    """


class GetVFolderTypesResponse(BaseRootResponseModel[list[str]]):
    """Response containing available virtual folder types.

    The handler returns a bare list of vfolder type names.
    e.g., ``["user", "group"]``
    """


class GetConfigResponse(BaseResponseModel):
    """Response containing etcd configuration value(s)."""

    result: Any = Field(
        description="The configuration value. A scalar for single key reads, or a dict for prefix reads."
    )


class SetConfigResponse(BaseResponseModel):
    """Response confirming etcd configuration update."""

    result: str = Field(description="Result status, typically 'ok'.")


class DeleteConfigResponse(BaseResponseModel):
    """Response confirming etcd configuration deletion."""

    result: str = Field(description="Result status, typically 'ok'.")


# --- scaling_group.py responses ---


class ListScalingGroupsResponse(BaseResponseModel):
    """Response containing available scaling groups."""

    scaling_groups: list[ScalingGroupDTO] = Field(
        description="List of scaling groups accessible to the requester."
    )


class GetWSProxyVersionResponse(BaseResponseModel):
    """Response containing the wsproxy API version for a scaling group."""

    wsproxy_version: int = Field(description="The wsproxy API version number.")


# --- resource.py responses ---


class ListPresetsResponse(BaseResponseModel):
    """Response containing resource presets."""

    presets: list[dict[str, Any]] = Field(description="List of resource preset configurations.")


class CheckPresetsResponse(BaseResponseModel):
    """Response containing resource presets with allocatability and usage information."""

    presets: list[dict[str, Any]] = Field(
        description="List of resource preset configurations with allocatability flags."
    )
    keypair_limits: dict[str, Any] = Field(
        description="Resource limits for the requesting keypair."
    )
    keypair_using: dict[str, Any] = Field(
        description="Resources currently in use by the requesting keypair."
    )
    keypair_remaining: dict[str, Any] = Field(
        description="Remaining resources available to the requesting keypair."
    )
    group_limits: dict[str, Any] = Field(description="Resource limits for the user group.")
    group_using: dict[str, Any] = Field(description="Resources currently in use by the user group.")
    group_remaining: dict[str, Any] = Field(
        description="Remaining resources available to the user group."
    )
    scaling_group_remaining: dict[str, Any] = Field(
        description="Remaining resources in the scaling group."
    )
    scaling_groups: dict[str, dict[str, Any]] = Field(
        description="Per-scaling-group resource breakdown with occupied and available slots."
    )


class RecalculateUsageResponse(BaseResponseModel):
    """Response confirming usage recalculation.

    The handler returns an empty dict ``{}``.
    """

    pass


class UsagePerMonthResponse(BaseRootResponseModel[list[Any]]):
    """Response containing monthly usage statistics.

    The handler returns a bare list of container usage records for the requested month.
    """


class UsagePerPeriodResponse(BaseRootResponseModel[list[Any]]):
    """Response containing usage statistics for a date range.

    The handler returns a bare list of container usage records for the requested period.
    """


class MonthStatsResponse(BaseRootResponseModel[list[Any]]):
    """Response containing time-binned session statistics over the last 30 days.

    The handler returns a bare list of time-binned (15 min) statistics
    for terminated sessions.
    """


class WatcherStatusResponse(BaseRootResponseModel[dict[str, Any]]):
    """Response containing the watcher status for an agent.

    The handler returns a bare dict of watcher status data.
    """


class WatcherAgentActionResponse(BaseRootResponseModel[dict[str, Any]]):
    """Response for watcher agent actions (start, stop, restart).

    The handler returns a bare dict of action result data.
    """


class GetContainerRegistriesResponse(BaseRootResponseModel[dict[str, Any]]):
    """Response containing registered container registries.

    The handler returns a bare dict mapping registry hostnames to their configurations.
    """
