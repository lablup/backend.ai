"""
Request DTOs for Scaling Group REST API.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = ("ListScalingGroupsQueryParams",)


class ListScalingGroupsQueryParams(BaseRequestModel):
    """Query parameters for listing available scaling groups."""

    group: str = Field(description="Group ID or name to filter scaling groups by")
