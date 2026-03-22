"""
Common types for scheduling history DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "DeploymentHistoryOrderField",
    "OrderDirection",
    "RouteHistoryOrderField",
    "SchedulingResultType",
    "SessionHistoryOrderField",
    "SubStepResultInfo",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


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
