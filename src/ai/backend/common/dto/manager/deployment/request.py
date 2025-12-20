"""
Request DTOs for deployment system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.model_deployment.types import (
    ModelDeploymentStatus,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.common.dto.manager.query import StringFilter

from .types import DeploymentOrder, RevisionOrder, RouteOrder

__all__ = (
    # Filters
    "DeploymentFilter",
    "RevisionFilter",
    "RouteFilter",
    # Search/List requests
    "SearchDeploymentsRequest",
    "SearchRevisionsRequest",
    "SearchRoutesRequest",
    # Update requests
    "UpdateDeploymentRequest",
    "UpdateRouteTrafficStatusRequest",
    # Path params
    "DeploymentPathParam",
    "RevisionPathParam",
    "RoutePathParam",
)


class DeploymentFilter(BaseRequestModel):
    """Filter for deployments."""

    name: Optional[StringFilter] = Field(default=None, description="Filter by name")
    project_id: Optional[UUID] = Field(default=None, description="Filter by project ID")
    domain_name: Optional[StringFilter] = Field(default=None, description="Filter by domain name")
    status: Optional[list[ModelDeploymentStatus]] = Field(
        default=None, description="Filter by deployment status"
    )


class RevisionFilter(BaseRequestModel):
    """Filter for revisions."""

    name: Optional[StringFilter] = Field(default=None, description="Filter by name")
    deployment_id: Optional[UUID] = Field(default=None, description="Filter by deployment ID")


class SearchDeploymentsRequest(BaseRequestModel):
    """Request body for searching deployments with filters, orders, and pagination."""

    filter: Optional[DeploymentFilter] = Field(default=None, description="Filter conditions")
    order: Optional[DeploymentOrder] = Field(default=None, description="Order specification")
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class SearchRevisionsRequest(BaseRequestModel):
    """Request body for searching revisions with filters, orders, and pagination."""

    filter: Optional[RevisionFilter] = Field(default=None, description="Filter conditions")
    order: Optional[RevisionOrder] = Field(default=None, description="Order specification")
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class UpdateDeploymentRequest(BaseRequestModel):
    """Request to update a deployment."""

    name: Optional[str] = Field(default=None, description="Updated deployment name")
    desired_replicas: Optional[int] = Field(
        default=None, ge=0, description="Updated desired replica count"
    )


class DeploymentPathParam(BaseRequestModel):
    """Path parameter for deployment ID."""

    deployment_id: UUID = Field(description="Deployment ID")


class RevisionPathParam(BaseRequestModel):
    """Path parameter for revision ID."""

    deployment_id: UUID = Field(description="Deployment ID")
    revision_id: UUID = Field(description="Revision ID")


class RouteFilter(BaseRequestModel):
    """Filter for routes."""

    deployment_id: Optional[UUID] = Field(default=None, description="Filter by deployment ID")
    statuses: Optional[list[RouteStatus]] = Field(
        default=None, description="Filter by route status"
    )
    traffic_statuses: Optional[list[RouteTrafficStatus]] = Field(
        default=None, description="Filter by traffic status"
    )


class SearchRoutesRequest(BaseRequestModel):
    """Request body for searching routes with filters, orders, and pagination."""

    filter: Optional[RouteFilter] = Field(default=None, description="Filter conditions")
    order: Optional[RouteOrder] = Field(default=None, description="Order specification")
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")
    # Cursor-based pagination (optional, for forward/backward navigation)
    cursor: Optional[str] = Field(default=None, description="Cursor for pagination")
    cursor_direction: Optional[str] = Field(
        default=None, description="Cursor direction: 'forward' or 'backward'"
    )


class UpdateRouteTrafficStatusRequest(BaseRequestModel):
    """Request to update route traffic status."""

    traffic_status: RouteTrafficStatus = Field(description="New traffic status")


class RoutePathParam(BaseRequestModel):
    """Path parameter for route ID."""

    deployment_id: UUID = Field(description="Deployment ID")
    route_id: UUID = Field(description="Route ID")
