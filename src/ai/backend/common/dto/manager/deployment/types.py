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
    UPDATED_AT = "updated_at"


class RevisionOrderField(enum.StrEnum):
    """Fields that can be used for ordering revisions."""

    NAME = "name"
    CREATED_AT = "created_at"


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
    "OrderDirection",
    "DeploymentOrderField",
    "RevisionOrderField",
    "RouteOrderField",
    "DeploymentOrder",
    "RevisionOrder",
    "RouteOrder",
)
