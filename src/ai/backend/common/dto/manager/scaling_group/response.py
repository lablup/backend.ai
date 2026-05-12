"""Response DTOs for scaling group API."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.types import BackendAISchema

__all__ = (
    "ScalingGroupItem",
    "ListScalingGroupsResponse",
    "WsproxyVersionResponse",
)


class ScalingGroupItem(BackendAISchema):
    """A single scaling group entry."""

    name: str = Field(description="Scaling group name")


class ListScalingGroupsResponse(BaseResponseModel):
    """Response for listing available scaling groups."""

    scaling_groups: list[ScalingGroupItem] = Field(
        description="List of scaling groups",
    )


class WsproxyVersionResponse(BaseResponseModel):
    """Response for getting wsproxy version."""

    wsproxy_version: str = Field(description="WSProxy API version")
