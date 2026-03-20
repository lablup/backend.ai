"""
Common types for scheduling history DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel, BaseResponseModel
from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "DeploymentHistoryOrderField",
    "DeploymentHistoryScopeDTO",
    "OrderDirection",
    "RouteHistoryOrderField",
    "RouteHistoryScopeDTO",
    "SchedulingResultType",
    "SessionHistoryOrderField",
    "SessionHistoryScopeDTO",
    "SubStepResultInfo",
)


class SchedulingResultType(StrEnum):
    """Result of a scheduling attempt."""

    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    STALE = "STALE"
    NEED_RETRY = "NEED_RETRY"
    EXPIRED = "EXPIRED"
    GIVE_UP = "GIVE_UP"
    SKIPPED = "SKIPPED"


class SessionHistoryOrderField(StrEnum):
    """Fields available for ordering session scheduling history."""

    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class DeploymentHistoryOrderField(StrEnum):
    """Fields available for ordering deployment scheduling history."""

    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class RouteHistoryOrderField(StrEnum):
    """Fields available for ordering route scheduling history."""

    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class SubStepResultInfo(BaseResponseModel):
    """Result of a single sub-step within a scheduling attempt."""

    step: str
    result: str
    error_code: str | None
    message: str | None
    started_at: datetime
    ended_at: datetime


class SessionHistoryScopeDTO(BaseRequestModel):
    """Scope for session scheduling history queries."""

    session_id: UUID = Field(description="Session ID to get history for.")


class DeploymentHistoryScopeDTO(BaseRequestModel):
    """Scope for deployment scheduling history queries."""

    deployment_id: UUID = Field(description="Deployment ID to get history for.")


class RouteHistoryScopeDTO(BaseRequestModel):
    """Scope for route scheduling history queries."""

    route_id: UUID = Field(description="Route ID to get history for.")
