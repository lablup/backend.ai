from __future__ import annotations

from typing import Any

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel, BaseRootResponseModel


class ListPresetsResponse(BaseResponseModel):
    """Response containing a list of resource presets."""

    presets: list[Any] = Field(description="List of resource presets")


class CheckPresetsResponse(BaseResponseModel):
    """Response containing preset allocatability information."""

    presets: list[Any] = Field(description="List of resource presets")
    keypair_limits: dict[str, Any] = Field(description="Keypair resource limits")
    keypair_using: dict[str, Any] = Field(description="Keypair resource usage")
    keypair_remaining: dict[str, Any] = Field(description="Keypair remaining resources")
    group_limits: dict[str, Any] = Field(description="Group resource limits")
    group_using: dict[str, Any] = Field(description="Group resource usage")
    group_remaining: dict[str, Any] = Field(description="Group remaining resources")
    scaling_group_remaining: dict[str, Any] = Field(description="Scaling group remaining resources")
    scaling_groups: dict[str, dict[str, Any]] = Field(description="Per-scaling-group resource info")


class EmptyResponse(BaseResponseModel):
    """Empty response body."""

    pass


class RawListResponse(BaseRootResponseModel[list[Any]]):
    """Response that serializes directly as a JSON array."""

    pass


class RawDictResponse(BaseRootResponseModel[dict[str, Any]]):
    """Response that serializes directly as a JSON object."""

    pass


class WatcherDataResponse(BaseRootResponseModel[dict[str, Any]]):
    """Response wrapping raw watcher data."""

    pass


class ContainerRegistriesResponse(BaseRootResponseModel[Any]):
    """Response wrapping container registry data."""

    pass
