"""
Response DTOs for scheduling history DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.pagination import PaginationInfo
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.common.identifier.replica_group_history import ReplicaGroupHistoryID

from .types import SubStepResultInfo

__all__ = (
    "AdminSearchDeploymentHistoriesPayload",
    "AdminSearchRouteHistoriesPayload",
    "AdminSearchSessionHistoriesPayload",
    "DeploymentHistoryNode",
    "KernelHistoryNode",
    "ListDeploymentHistoryPayload",
    "ListRouteHistoryPayload",
    "ListSessionHistoryPayload",
    "ReplicaGroupHistoryNode",
    "RouteHistoryNode",
    "SearchKernelHistoriesPayload",
    "SearchReplicaGroupHistoriesPayload",
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


class KernelHistoryNode(BaseResponseModel):
    """Node model representing a kernel scheduling history record.

    Has no ``sub_steps``: the ``kernel_scheduling_history`` table carries no such column.
    """

    id: UUID = Field(description="History record ID")
    kernel_id: UUID = Field(description="Kernel ID this history belongs to")
    session_id: UUID = Field(description="Session owning the kernel")
    phase: str = Field(description="Scheduling phase")
    from_status: str | None = Field(default=None, description="Status before transition")
    to_status: str | None = Field(default=None, description="Status after transition")
    result: str = Field(description="Result of the scheduling attempt")
    error_code: str | None = Field(default=None, description="Error code if scheduling failed")
    message: str | None = Field(default=None, description="Human-readable message or error detail")
    attempts: int = Field(description="Number of scheduling attempts made")
    created_at: datetime = Field(description="Timestamp when the history record was created")
    updated_at: datetime = Field(description="Timestamp when the history record was last updated")


class DeploymentHistoryNode(BaseResponseModel):
    """Node model representing a deployment scheduling history record.

    ``category`` separates rows produced by lifecycle handlers (monotonic
    lifecycle progression) from rows produced by scaling handlers
    (reconciling replica count while lifecycle stays put). Clients
    filter / group by this axis when rendering the history.
    """

    id: UUID = Field(description="History record ID")
    deployment_id: UUID = Field(description="Deployment ID this history belongs to")
    category: str = Field(
        description="Handler category: 'lifecycle' or 'scaling' (HEALTH reserved)"
    )
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
    category: str = Field(description="Handler category: 'lifecycle' or 'health'")
    phase: str = Field(description="Scheduling phase")
    from_status: str | None = Field(default=None, description="Lifecycle status before transition")
    to_status: str | None = Field(default=None, description="Lifecycle status after transition")
    from_sub_status: str | None = Field(default=None, description="Sub-status before transition")
    to_sub_status: str | None = Field(default=None, description="Sub-status after transition")
    result: str = Field(description="Result of the scheduling attempt")
    error_code: str | None = Field(default=None, description="Error code if scheduling failed")
    message: str | None = Field(default=None, description="Human-readable message or error detail")
    sub_steps: list[SubStepResultInfo] = Field(
        default_factory=list, description="Sub-step results within this scheduling attempt"
    )
    attempts: int = Field(description="Number of scheduling attempts made")
    created_at: datetime = Field(description="Timestamp when the history record was created")
    updated_at: datetime = Field(description="Timestamp when the history record was last updated")


class ReplicaGroupHistoryNode(BaseResponseModel):
    """Node model representing a replica-group scheduling history record.

    ``category`` separates rows produced by lifecycle handlers (monotonic
    lifecycle progression) from rows produced by scaling handlers
    (reconciling replica count while lifecycle stays put). Clients filter /
    group by this axis when rendering the history.
    """

    id: ReplicaGroupHistoryID = Field(description="History record ID")
    replica_group_id: ReplicaGroupID = Field(description="Replica group this history belongs to")
    deployment_id: DeploymentID = Field(description="Deployment the replica group belongs to")
    category: str = Field(description="Handler category: 'lifecycle' or 'scaling'")
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


class AdminSearchSessionHistoriesPayload(BaseResponseModel):
    """Payload for admin search of session scheduling histories."""

    items: list[SessionHistoryNode] = Field(description="List of session history nodes.")
    total_count: int = Field(description="Total number of records matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")


class SearchKernelHistoriesPayload(BaseResponseModel):
    """Payload for admin and scoped search of kernel scheduling histories."""

    items: list[KernelHistoryNode] = Field(description="List of kernel history nodes.")
    total_count: int = Field(description="Total number of records matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")


class AdminSearchDeploymentHistoriesPayload(BaseResponseModel):
    """Payload for admin search of deployment histories."""

    items: list[DeploymentHistoryNode] = Field(description="List of deployment history nodes.")
    total_count: int = Field(description="Total number of records matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")


class AdminSearchRouteHistoriesPayload(BaseResponseModel):
    """Payload for admin search of route histories."""

    items: list[RouteHistoryNode] = Field(description="List of route history nodes.")
    total_count: int = Field(description="Total number of records matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")


class SearchReplicaGroupHistoriesPayload(BaseResponseModel):
    """Payload for admin and scoped search of replica-group scheduling histories."""

    items: list[ReplicaGroupHistoryNode] = Field(description="List of replica-group history nodes.")
    total_count: int = Field(description="Total number of records matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")
