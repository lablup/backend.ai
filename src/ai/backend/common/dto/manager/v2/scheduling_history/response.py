"""
Response DTOs for scheduling history DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.pagination import PaginationInfo

from .types import SubStepResultInfo

__all__ = (
    "DeploymentHistoryNode",
    "ListDeploymentHistoryPayload",
    "ListRouteHistoryPayload",
    "ListSessionHistoryPayload",
    "RouteHistoryNode",
    "SessionHistoryNode",
)


class SessionHistoryNode(BaseResponseModel):
    """Node model representing a session scheduling history record."""

    id: UUID = Field(description="History record ID")
    session_id: UUID = Field(description="Session ID this history belongs to")
    phase: str = Field(description="Scheduling phase")
    from_status: str | None = Field(default=None, description="Status before transition")
    to_status: str | None = Field(default=None, description="Status after transition")
    result: str = Field(description="Result of the scheduling attempt")
    error_code: str | None = Field(default=None, description="Error code if scheduling failed")
    message: str | None = Field(default=None, description="Human-readable message or error detail")
    sub_steps: list[SubStepResultInfo] = Field(
        default_factory=list, description="Sub-step results within this scheduling attempt"
    )
    attempts: int = Field(description="Number of scheduling attempts made")
    created_at: datetime = Field(description="Timestamp when the history record was created")
    updated_at: datetime = Field(description="Timestamp when the history record was last updated")


class DeploymentHistoryNode(BaseResponseModel):
    """Node model representing a deployment scheduling history record."""

    id: UUID = Field(description="History record ID")
    deployment_id: UUID = Field(description="Deployment ID this history belongs to")
    phase: str = Field(description="Scheduling phase")
    from_status: str | None = Field(default=None, description="Status before transition")
    to_status: str | None = Field(default=None, description="Status after transition")
    result: str = Field(description="Result of the scheduling attempt")
    error_code: str | None = Field(default=None, description="Error code if scheduling failed")
    message: str | None = Field(default=None, description="Human-readable message or error detail")
    sub_steps: list[SubStepResultInfo] = Field(
        default_factory=list, description="Sub-step results within this scheduling attempt"
    )
    attempts: int = Field(description="Number of scheduling attempts made")
    created_at: datetime = Field(description="Timestamp when the history record was created")
    updated_at: datetime = Field(description="Timestamp when the history record was last updated")


class RouteHistoryNode(BaseResponseModel):
    """Node model representing a route scheduling history record."""

    id: UUID = Field(description="History record ID")
    route_id: UUID = Field(description="Route ID this history belongs to")
    deployment_id: UUID = Field(description="Deployment ID the route belongs to")
    phase: str = Field(description="Scheduling phase")
    from_status: str | None = Field(default=None, description="Status before transition")
    to_status: str | None = Field(default=None, description="Status after transition")
    result: str = Field(description="Result of the scheduling attempt")
    error_code: str | None = Field(default=None, description="Error code if scheduling failed")
    message: str | None = Field(default=None, description="Human-readable message or error detail")
    sub_steps: list[SubStepResultInfo] = Field(
        default_factory=list, description="Sub-step results within this scheduling attempt"
    )
    attempts: int = Field(description="Number of scheduling attempts made")
    created_at: datetime = Field(description="Timestamp when the history record was created")
    updated_at: datetime = Field(description="Timestamp when the history record was last updated")


class ListSessionHistoryPayload(BaseResponseModel):
    """Payload for listing session scheduling history."""

    items: list[SessionHistoryNode] = Field(description="List of session history records")
    pagination: PaginationInfo = Field(description="Pagination information")


class ListDeploymentHistoryPayload(BaseResponseModel):
    """Payload for listing deployment scheduling history."""

    items: list[DeploymentHistoryNode] = Field(description="List of deployment history records")
    pagination: PaginationInfo = Field(description="Pagination information")


class ListRouteHistoryPayload(BaseResponseModel):
    """Payload for listing route scheduling history."""

    items: list[RouteHistoryNode] = Field(description="List of route history records")
    pagination: PaginationInfo = Field(description="Pagination information")
