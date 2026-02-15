"""
Response DTOs for Scaling Group REST API.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "ScalingGroupDTO",
    "ListScalingGroupsResponse",
    "GetWsproxyVersionResponse",
)


class ScalingGroupDTO(BaseModel):
    """DTO for scaling group data."""

    name: str = Field(description="Scaling group name")


class ListScalingGroupsResponse(BaseResponseModel):
    """Response for listing available scaling groups."""

    scaling_groups: list[ScalingGroupDTO] = Field(description="List of scaling groups")


class GetWsproxyVersionResponse(BaseResponseModel):
    """Response for getting the wsproxy version of a scaling group."""

    wsproxy_version: str = Field(description="WSProxy API version")
