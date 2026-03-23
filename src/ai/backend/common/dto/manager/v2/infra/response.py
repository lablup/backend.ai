"""
Response DTOs for infra DTO v2.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "CheckPresetsPayload",
    "ContainerRegistriesPayload",
    "ListPresetsPayload",
    "ListScalingGroupsPayload",
    "ResourcePresetNode",
    "ScalingGroupNode",
    "UsagePayload",
    "WSProxyVersionPayload",
    "WatcherActionPayload",
    "WatcherStatusPayload",
)


class ScalingGroupNode(BaseResponseModel):
    """Node model representing a scaling group."""

    name: str = Field(description="Name of the scaling group.")


class ResourcePresetNode(BaseResponseModel):
    """Node model representing a resource preset configuration."""

    name: str = Field(description="Name of the resource preset.")
    resource_slots: dict[str, Any] = Field(description="Resource slot allocations.")
    shared_memory: str | None = Field(default=None, description="Shared memory size if configured.")


class ListScalingGroupsPayload(BaseResponseModel):
    """Payload for listing scaling groups."""

    scaling_groups: list[ScalingGroupNode] = Field(
        description="List of scaling groups accessible to the requester."
    )


class WSProxyVersionPayload(BaseResponseModel):
    """Payload containing the wsproxy API version for a scaling group."""

    wsproxy_version: int = Field(description="The wsproxy API version number.")


class ListPresetsPayload(BaseResponseModel):
    """Payload containing resource presets."""

    presets: list[dict[str, Any]] = Field(description="List of resource preset configurations.")


class CheckPresetsPayload(BaseResponseModel):
    """Payload containing resource presets with allocatability and usage information."""

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


class UsagePayload(BaseResponseModel):
    """Payload containing usage statistics records."""

    records: list[Any] = Field(description="List of usage records.")


class WatcherStatusPayload(BaseResponseModel):
    """Payload containing the watcher status for an agent."""

    status: dict[str, Any] = Field(description="Watcher status data.")


class WatcherActionPayload(BaseResponseModel):
    """Payload for watcher agent actions (start, stop, restart)."""

    result: dict[str, Any] = Field(description="Action result data.")


class ContainerRegistriesPayload(BaseResponseModel):
    """Payload containing registered container registries."""

    registries: dict[str, Any] = Field(
        description="Mapping of registry hostnames to their configurations."
    )
