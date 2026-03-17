"""
Request DTOs for scheduling history DTO v2.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter

from .types import (
    DeploymentHistoryOrderField,
    OrderDirection,
    RouteHistoryOrderField,
    SchedulingResultType,
    SessionHistoryOrderField,
)

__all__ = (
    "AdminSearchDeploymentHistoriesInput",
    "AdminSearchRouteHistoriesInput",
    "AdminSearchSessionHistoriesInput",
    "DeploymentHistoryFilter",
    "DeploymentHistoryOrder",
    "RouteHistoryFilter",
    "RouteHistoryOrder",
    "SearchDeploymentHistoryInput",
    "SearchRouteHistoryInput",
    "SearchSessionHistoryInput",
    "SessionHistoryFilter",
    "SessionHistoryOrder",
)


class SessionHistoryFilter(BaseRequestModel):
    """Filter conditions for session scheduling history search."""

    session_id: UUIDFilter | None = Field(default=None, description="Filter by session ID")
    phase: StringFilter | None = Field(default=None, description="Filter by scheduling phase")
    from_status: list[str] | None = Field(default=None, description="Filter by from_status values")
    to_status: list[str] | None = Field(default=None, description="Filter by to_status values")
    result: list[SchedulingResultType] | None = Field(
        default=None, description="Filter by scheduling result"
    )
    error_code: StringFilter | None = Field(default=None, description="Filter by error code")
    message: StringFilter | None = Field(default=None, description="Filter by message")


class SessionHistoryOrder(BaseRequestModel):
    """Order specification for session scheduling history."""

    field: SessionHistoryOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.DESC, description="Order direction")


class SearchSessionHistoryInput(BaseRequestModel):
    """Input for searching session scheduling history with filters, orders, and pagination."""

    filter: SessionHistoryFilter | None = Field(default=None, description="Filter conditions")
    order: list[SessionHistoryOrder] | None = Field(
        default=None, description="Order specifications"
    )
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class DeploymentHistoryFilter(BaseRequestModel):
    """Filter conditions for deployment scheduling history search."""

    deployment_id: UUIDFilter | None = Field(default=None, description="Filter by deployment ID")
    phase: StringFilter | None = Field(default=None, description="Filter by scheduling phase")
    from_status: list[str] | None = Field(default=None, description="Filter by from_status values")
    to_status: list[str] | None = Field(default=None, description="Filter by to_status values")
    result: list[SchedulingResultType] | None = Field(
        default=None, description="Filter by scheduling result"
    )
    error_code: StringFilter | None = Field(default=None, description="Filter by error code")
    message: StringFilter | None = Field(default=None, description="Filter by message")


class DeploymentHistoryOrder(BaseRequestModel):
    """Order specification for deployment scheduling history."""

    field: DeploymentHistoryOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.DESC, description="Order direction")


class SearchDeploymentHistoryInput(BaseRequestModel):
    """Input for searching deployment scheduling history with filters, orders, and pagination."""

    filter: DeploymentHistoryFilter | None = Field(default=None, description="Filter conditions")
    order: list[DeploymentHistoryOrder] | None = Field(
        default=None, description="Order specifications"
    )
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class RouteHistoryFilter(BaseRequestModel):
    """Filter conditions for route scheduling history search."""

    route_id: UUIDFilter | None = Field(default=None, description="Filter by route ID")
    deployment_id: UUIDFilter | None = Field(default=None, description="Filter by deployment ID")
    phase: StringFilter | None = Field(default=None, description="Filter by scheduling phase")
    from_status: list[str] | None = Field(default=None, description="Filter by from_status values")
    to_status: list[str] | None = Field(default=None, description="Filter by to_status values")
    result: list[SchedulingResultType] | None = Field(
        default=None, description="Filter by scheduling result"
    )
    error_code: StringFilter | None = Field(default=None, description="Filter by error code")
    message: StringFilter | None = Field(default=None, description="Filter by message")


class RouteHistoryOrder(BaseRequestModel):
    """Order specification for route scheduling history."""

    field: RouteHistoryOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.DESC, description="Order direction")


class SearchRouteHistoryInput(BaseRequestModel):
    """Input for searching route scheduling history with filters, orders, and pagination."""

    filter: RouteHistoryFilter | None = Field(default=None, description="Filter conditions")
    order: list[RouteHistoryOrder] | None = Field(default=None, description="Order specifications")
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class AdminSearchSessionHistoriesInput(BaseRequestModel):
    """Input for admin search of session scheduling histories."""

    filter: SessionHistoryFilter | None = Field(default=None, description="Filter conditions")
    order: list[SessionHistoryOrder] | None = Field(
        default=None, description="Order specifications"
    )
    first: int | None = Field(default=None, description="Cursor pagination: number of items")
    after: str | None = Field(default=None, description="Cursor pagination: after cursor")
    last: int | None = Field(default=None, description="Cursor pagination: last N items")
    before: str | None = Field(default=None, description="Cursor pagination: before cursor")
    limit: int | None = Field(default=None, description="Offset pagination: maximum items")
    offset: int | None = Field(default=None, description="Offset pagination: number to skip")


class AdminSearchDeploymentHistoriesInput(BaseRequestModel):
    """Input for admin search of deployment histories."""

    filter: DeploymentHistoryFilter | None = Field(default=None, description="Filter conditions")
    order: list[DeploymentHistoryOrder] | None = Field(
        default=None, description="Order specifications"
    )
    first: int | None = Field(default=None, description="Cursor pagination: number of items")
    after: str | None = Field(default=None, description="Cursor pagination: after cursor")
    last: int | None = Field(default=None, description="Cursor pagination: last N items")
    before: str | None = Field(default=None, description="Cursor pagination: before cursor")
    limit: int | None = Field(default=None, description="Offset pagination: maximum items")
    offset: int | None = Field(default=None, description="Offset pagination: number to skip")


class AdminSearchRouteHistoriesInput(BaseRequestModel):
    """Input for admin search of route histories."""

    filter: RouteHistoryFilter | None = Field(default=None, description="Filter conditions")
    order: list[RouteHistoryOrder] | None = Field(default=None, description="Order specifications")
    first: int | None = Field(default=None, description="Cursor pagination: number of items")
    after: str | None = Field(default=None, description="Cursor pagination: after cursor")
    last: int | None = Field(default=None, description="Cursor pagination: last N items")
    before: str | None = Field(default=None, description="Cursor pagination: before cursor")
    limit: int | None = Field(default=None, description="Offset pagination: maximum items")
    offset: int | None = Field(default=None, description="Offset pagination: number to skip")
