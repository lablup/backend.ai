"""Request DTOs for scaling group API."""

from __future__ import annotations

from pydantic import AliasChoices, Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    "ListScalingGroupsRequest",
    "WsproxyVersionPathParam",
    "WsproxyVersionQueryParam",
)


class ListScalingGroupsRequest(BaseRequestModel):
    """Query parameters for listing available scaling groups."""

    group: str = Field(
        description="Group ID or name",
        validation_alias=AliasChoices("group", "group_id", "group_name"),
    )


class WsproxyVersionPathParam(BaseRequestModel):
    """Path parameters for getting wsproxy version."""

    scaling_group: str = Field(description="Scaling group name")


class WsproxyVersionQueryParam(BaseRequestModel):
    """Query parameters for getting wsproxy version."""

    group: str | None = Field(
        default=None,
        description="Group ID or name",
        validation_alias=AliasChoices("group", "group_id", "group_name"),
    )
