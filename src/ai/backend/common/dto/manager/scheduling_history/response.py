from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "PaginationInfo",
    "SubStepResultDTO",
    "SessionHistoryDTO",
    "DeploymentHistoryDTO",
    "RouteHistoryDTO",
    "ListSessionHistoryResponse",
    "ListDeploymentHistoryResponse",
    "ListRouteHistoryResponse",
)


class PaginationInfo(BaseModel):
    """Pagination information."""

    total: int = Field(description="Total number of items")
    offset: int = Field(description="Number of items skipped")
    limit: int | None = Field(default=None, description="Maximum items returned")


class SubStepResultDTO(BaseResponseModel):
    """Sub-step result DTO."""

    step: str
    result: str
    error_code: str | None = None
    message: str | None = None
    started_at: datetime
    ended_at: datetime


class SessionHistoryDTO(BaseResponseModel):
    """Session scheduling history DTO."""

    id: UUID
    session_id: UUID
    phase: str
    from_status: str | None = None
    to_status: str | None = None
    result: str
    error_code: str | None = None
    message: str | None = None
    sub_steps: list[SubStepResultDTO] = Field(default_factory=list)
    attempts: int
    created_at: datetime
    updated_at: datetime


class DeploymentHistoryDTO(BaseResponseModel):
    """Deployment history DTO."""

    id: UUID
    deployment_id: UUID
    phase: str
    from_status: str | None = None
    to_status: str | None = None
    result: str
    error_code: str | None = None
    message: str | None = None
    sub_steps: list[SubStepResultDTO] = Field(default_factory=list)
    attempts: int
    created_at: datetime
    updated_at: datetime


class RouteHistoryDTO(BaseResponseModel):
    """Route history DTO."""

    id: UUID
    route_id: UUID
    deployment_id: UUID
    phase: str
    from_status: str | None = None
    to_status: str | None = None
    result: str
    error_code: str | None = None
    message: str | None = None
    sub_steps: list[SubStepResultDTO] = Field(default_factory=list)
    attempts: int
    created_at: datetime
    updated_at: datetime


class ListSessionHistoryResponse(BaseResponseModel):
    """Response for listing session scheduling history."""

    items: list[SessionHistoryDTO] = Field(description="List of history records")
    pagination: PaginationInfo = Field(description="Pagination information")


class ListDeploymentHistoryResponse(BaseResponseModel):
    """Response for listing deployment history."""

    items: list[DeploymentHistoryDTO] = Field(description="List of history records")
    pagination: PaginationInfo = Field(description="Pagination information")


class ListRouteHistoryResponse(BaseResponseModel):
    """Response for listing route history."""

    items: list[RouteHistoryDTO] = Field(description="List of history records")
    pagination: PaginationInfo = Field(description="Pagination information")
