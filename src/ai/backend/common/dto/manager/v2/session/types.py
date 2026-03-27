"""
Common types for Session DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "ClusterModeEnum",
    "CreateSessionTypeEnum",
    "OrderDirection",
    "SessionOrderField",
    "SessionResultEnum",
    "SessionStatusEnum",
    "SessionStatusFilter",
    "SessionTypeEnum",
)


class SessionStatusEnum(StrEnum):
    """Full set of session lifecycle statuses for DTO filtering."""

    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    PREPARING = "PREPARING"
    PULLING = "PULLING"
    PREPARED = "PREPARED"
    CREATING = "CREATING"
    RUNNING = "RUNNING"
    RESTARTING = "RESTARTING"
    RUNNING_DEGRADED = "RUNNING_DEGRADED"
    DEPRIORITIZING = "DEPRIORITIZING"
    TERMINATING = "TERMINATING"
    TERMINATED = "TERMINATED"
    ERROR = "ERROR"
    CANCELLED = "CANCELLED"


class SessionTypeEnum(StrEnum):
    """Session types for DTO filtering."""

    INTERACTIVE = "interactive"
    BATCH = "batch"
    INFERENCE = "inference"
    SYSTEM = "system"


class SessionResultEnum(StrEnum):
    """Session result values."""

    UNDEFINED = "undefined"
    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"


class SessionOrderField(StrEnum):
    """Fields available for ordering sessions."""

    CREATED_AT = "created_at"
    TERMINATED_AT = "terminated_at"
    STATUS = "status"
    ID = "id"
    NAME = "name"


class CreateSessionTypeEnum(StrEnum):
    """Session types allowed for user-initiated creation."""

    INTERACTIVE = "interactive"
    BATCH = "batch"


class ClusterModeEnum(StrEnum):
    """Cluster networking modes."""

    SINGLE_NODE = "single-node"
    MULTI_NODE = "multi-node"


class SessionStatusFilter(BaseRequestModel):
    """Filter for session status values."""

    in_: list[SessionStatusEnum] | None = None
    not_in: list[SessionStatusEnum] | None = None
