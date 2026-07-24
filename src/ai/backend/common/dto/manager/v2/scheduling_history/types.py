"""
Common types for scheduling history DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Self
from uuid import UUID

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel, BaseResponseModel
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope

__all__ = (
    "DeploymentHistoryOrderField",
    "DeploymentHistoryScopeDTO",
    "KernelHistoryOrderField",
    "KernelHistoryScopeDTO",
    "OrderDirection",
    "ReplicaGroupHistoryCategoryType",
    "ReplicaGroupHistoryOrderField",
    "ReplicaGroupHistoryScopeDTO",
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


class KernelHistoryOrderField(StrEnum):
    """Fields available for ordering kernel scheduling history."""

    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    PHASE = "phase"
    FROM_STATUS = "from_status"
    TO_STATUS = "to_status"
    RESULT = "result"
    ATTEMPTS = "attempts"


class DeploymentHistoryOrderField(StrEnum):
    """Fields available for ordering deployment scheduling history."""

    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class RouteHistoryOrderField(StrEnum):
    """Fields available for ordering route scheduling history."""

    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class ReplicaGroupHistoryCategoryType(StrEnum):
    """Handler category a replica-group history row was produced by."""

    LIFECYCLE = "lifecycle"
    SCALING = "scaling"


class ReplicaGroupHistoryOrderField(StrEnum):
    """Fields available for ordering replica-group scheduling history."""

    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    PHASE = "phase"
    FROM_STATUS = "from_status"
    TO_STATUS = "to_status"
    RESULT = "result"
    ATTEMPTS = "attempts"


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


class KernelHistoryScopeDTO(BaseRequestModel):
    """Scope for kernel scheduling history queries.

    Each list is OR'd internally and across categories. Raises an error if every
    field is empty. The scoped search is still a single-target scope action, so
    only one item is dispatchable today; the list shape keeps the wire contract
    stable for the multi-target case.
    """

    kernel: list[UUIDScope] | None = Field(
        default=None, description="Kernel IDs to get history for."
    )
    session: list[UUIDScope] | None = Field(
        default=None,
        description="Session IDs to get the history of every owned kernel for.",
    )

    @model_validator(mode="after")
    def _require_non_empty(self) -> Self:
        if not self.kernel and not self.session:
            raise ValueError(
                "KernelHistoryScopeDTO requires a non-empty value for 'kernel' or 'session'"
            )
        return self


class DeploymentHistoryScopeDTO(BaseRequestModel):
    """Scope for deployment scheduling history queries."""

    deployment_id: UUID = Field(description="Deployment ID to get history for.")


class RouteHistoryScopeDTO(BaseRequestModel):
    """Scope for route scheduling history queries."""

    route_id: UUID = Field(description="Route ID to get history for.")


class ReplicaGroupHistoryScopeDTO(BaseRequestModel):
    """Scope for replica-group scheduling history queries.

    Each list is OR'd internally and across categories. Raises an error if every
    field is empty. The scoped search is still a single-target scope action, so
    only one item is dispatchable today; the list shape keeps the wire contract
    stable for the multi-target case.
    """

    replica_group: list[UUIDScope] | None = Field(
        default=None, description="Replica group IDs to get history for."
    )
    deployment: list[UUIDScope] | None = Field(
        default=None,
        description="Deployment IDs to get the history of every owned replica group for.",
    )

    @model_validator(mode="after")
    def _require_non_empty(self) -> Self:
        if not self.replica_group and not self.deployment:
            raise ValueError(
                "ReplicaGroupHistoryScopeDTO requires a non-empty value for "
                "'replica_group' or 'deployment'"
            )
        return self
