"""
Common types for deployment DTOs.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

import enum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel


class OrderDirection(enum.StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class DeploymentOrderField(enum.StrEnum):
    """Fields that can be used for ordering deployments."""

    NAME = "name"
    CREATED_AT = "created_at"
    DESTROYED_AT = "destroyed_at"
    DOMAIN = "domain"
    PROJECT = "project"
    RESOURCE_GROUP = "resource_group"
    TAG = "tag"


class RevisionOrderField(enum.StrEnum):
    """Fields that can be used for ordering revisions."""

    REVISION_NUMBER = "revision_number"
    CREATED_AT = "created_at"
    RESOURCE_GROUP = "resource_group"
    CLUSTER_MODE = "cluster_mode"
    RUNTIME_VARIANT = "runtime_variant"


class RouteOrderField(enum.StrEnum):
    """Fields that can be used for ordering routes."""

    CREATED_AT = "created_at"
    STATUS = "status"
    TRAFFIC_RATIO = "traffic_ratio"


class DeploymentOrder(BaseRequestModel):
    """Order specification for deployments."""

    field: DeploymentOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


class RevisionOrder(BaseRequestModel):
    """Order specification for revisions."""

    field: RevisionOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


class RouteOrder(BaseRequestModel):
    """Order specification for routes."""

    field: RouteOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


__all__ = (
    "DeploymentOrder",
    "DeploymentOrderField",
    "OrderDirection",
    "RevisionOrder",
    "RevisionOrderField",
    "RouteOrder",
    "RouteOrderField",
)
