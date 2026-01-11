from __future__ import annotations

from enum import StrEnum
from typing import Optional

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter

__all__ = (
    "OrderDirection",
    "SchedulingResultType",
    "SessionHistoryOrderField",
    "SessionHistoryFilter",
    "SessionHistoryOrder",
    "DeploymentHistoryOrderField",
    "DeploymentHistoryFilter",
    "DeploymentHistoryOrder",
    "RouteHistoryOrderField",
    "RouteHistoryFilter",
    "RouteHistoryOrder",
)


class OrderDirection(StrEnum):
    ASC = "asc"
    DESC = "desc"


class SchedulingResultType(StrEnum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    STALE = "STALE"


class SessionHistoryOrderField(StrEnum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class SessionHistoryFilter(BaseRequestModel):
    """Filter for session scheduling history."""

    session_id: Optional[UUIDFilter] = Field(default=None, description="Filter by session ID")
    result: Optional[list[SchedulingResultType]] = Field(
        default=None, description="Filter by result (SUCCESS, FAILURE, STALE)"
    )
    error_code: Optional[StringFilter] = Field(default=None, description="Filter by error code")


class SessionHistoryOrder(BaseRequestModel):
    """Order specification for session scheduling history."""

    field: SessionHistoryOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.DESC, description="Order direction")


class DeploymentHistoryOrderField(StrEnum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class DeploymentHistoryFilter(BaseRequestModel):
    """Filter for deployment history."""

    deployment_id: Optional[UUIDFilter] = Field(default=None, description="Filter by deployment ID")
    result: Optional[list[SchedulingResultType]] = Field(
        default=None, description="Filter by result"
    )
    error_code: Optional[StringFilter] = Field(default=None, description="Filter by error code")


class DeploymentHistoryOrder(BaseRequestModel):
    """Order specification for deployment history."""

    field: DeploymentHistoryOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.DESC, description="Order direction")


class RouteHistoryOrderField(StrEnum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class RouteHistoryFilter(BaseRequestModel):
    """Filter for route history."""

    route_id: Optional[UUIDFilter] = Field(default=None, description="Filter by route ID")
    deployment_id: Optional[UUIDFilter] = Field(default=None, description="Filter by deployment ID")
    result: Optional[list[SchedulingResultType]] = Field(
        default=None, description="Filter by result"
    )
    error_code: Optional[StringFilter] = Field(default=None, description="Filter by error code")


class RouteHistoryOrder(BaseRequestModel):
    """Order specification for route history."""

    field: RouteHistoryOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.DESC, description="Order direction")
