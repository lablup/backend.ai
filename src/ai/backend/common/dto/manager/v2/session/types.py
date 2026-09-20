"""
Common types for Session DTO v2.
"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import EnumFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope

__all__ = (
    "ClusterModeEnum",
    "CreateSessionTypeEnum",
    "OrderDirection",
    "ProjectSessionScope",
    "SessionOrderField",
    "SessionResultEnum",
    "SessionStatusEnum",
    "SessionResultFilter",
    "SessionStatusFilter",
    "SessionTypeEnum",
    "SessionTypeFilter",
    "SessionUsedBy",
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
    RESERVED = "RESERVED"
    PREEMPTED = "PREEMPTED"
    RESCHEDULING = "RESCHEDULING"
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
    CREATION_ID = "creation_id"
    SESSION_TYPE = "session_type"
    PRIORITY = "priority"
    TIER = "tier"
    JOB_PRIORITY = "job_priority"
    IS_PREEMPTIBLE = "is_preemptible"
    CLUSTER_SIZE = "cluster_size"
    RESOURCE_GROUP_NAME = "resource_group_name"
    DOMAIN_NAME = "domain_name"
    PROJECT_ID = "project_id"
    USER_ID = "user_id"
    ACCESS_KEY = "access_key"
    TAG = "tag"
    USE_HOST_NETWORK = "use_host_network"
    BATCH_TIMEOUT = "batch_timeout"
    STARTS_AT = "starts_at"
    RESULT = "result"
    NETWORK_TYPE = "network_type"
    NETWORK_ID = "network_id"
    REPLICA_ID = "replica_id"


class CreateSessionTypeEnum(StrEnum):
    """Session types allowed for user-initiated creation."""

    INTERACTIVE = "interactive"
    BATCH = "batch"


class ClusterModeEnum(StrEnum):
    """Cluster networking modes."""

    SINGLE_NODE = "single-node"
    MULTI_NODE = "multi-node"


class SessionStatusFilter(EnumFilter[SessionStatusEnum]):
    """Filter for session status values."""


class SessionTypeFilter(EnumFilter[SessionTypeEnum]):
    """Filter for session type values."""


class SessionResultFilter(EnumFilter[SessionResultEnum]):
    """Filter for session result values."""


class NetworkTypeEnum(StrEnum):
    """Inter-container network types a session may use."""

    VOLATILE = "volatile"
    PERSISTENT = "persistent"
    HOST = "host"


class NetworkTypeFilter(EnumFilter[NetworkTypeEnum]):
    """Filter for session network type values."""


class SessionUsedBy(BaseRequestModel):
    """Entities whose use narrows the sessions read; every id is AND-ed.

    An entity the caller cannot read refuses the request. Sessions the caller cannot read
    are left out even when a listed entity uses them.
    """

    deployment: list[UUID] | None = Field(
        default=None, description="Deployments whose route rows the session serves as a replica"
    )
    agent: list[UUID] | None = Field(
        default=None, description="Agents running a kernel of the session"
    )
    resource_group: list[UUID] | None = Field(
        default=None, description="Resource groups the session runs in"
    )


class ProjectSessionScope(BaseRequestModel):
    """Scope for project-level session operations."""

    project_id: UUID = Field(description="Project UUID to scope the operation.")


class SessionScope(BaseRequestModel):
    """Scope for the scoped session query.

    Each list is OR'd internally and across lists. Raises an error if every field is
    empty.
    """

    domain: list[UUIDScope] | None = Field(
        default=None, description="Domains whose sessions are being read"
    )
    project: list[UUIDScope] | None = Field(
        default=None, description="Projects whose sessions are being read"
    )
    user: list[UUIDScope] | None = Field(
        default=None, description="Users whose sessions are being read"
    )

    @model_validator(mode="after")
    def _require_non_empty(self) -> SessionScope:
        if not self.domain and not self.project and not self.user:
            raise ValueError(
                "SessionScope requires a non-empty value for 'domain', 'project' or 'user'"
            )
        return self
