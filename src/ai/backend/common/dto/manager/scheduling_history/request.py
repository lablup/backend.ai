from __future__ import annotations

from typing import Optional

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

from .types import (
    DeploymentHistoryFilter,
    DeploymentHistoryOrder,
    RouteHistoryFilter,
    RouteHistoryOrder,
    SessionHistoryFilter,
    SessionHistoryOrder,
)

__all__ = (
    "SearchSessionHistoryRequest",
    "SearchDeploymentHistoryRequest",
    "SearchRouteHistoryRequest",
)


class SearchSessionHistoryRequest(BaseRequestModel):
    """Request body for searching session scheduling history."""

    filter: Optional[SessionHistoryFilter] = Field(default=None, description="Filter conditions")
    order: Optional[list[SessionHistoryOrder]] = Field(
        default=None, description="Order specifications"
    )
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class SearchDeploymentHistoryRequest(BaseRequestModel):
    """Request body for searching deployment history."""

    filter: Optional[DeploymentHistoryFilter] = Field(default=None, description="Filter conditions")
    order: Optional[list[DeploymentHistoryOrder]] = Field(
        default=None, description="Order specifications"
    )
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class SearchRouteHistoryRequest(BaseRequestModel):
    """Request body for searching route history."""

    filter: Optional[RouteHistoryFilter] = Field(default=None, description="Filter conditions")
    order: Optional[list[RouteHistoryOrder]] = Field(
        default=None, description="Order specifications"
    )
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")
