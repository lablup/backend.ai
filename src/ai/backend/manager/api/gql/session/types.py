"""GraphQL types for session management."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Self

import strawberry
from strawberry import ID
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.manager.api.gql.base import OrderDirection, UUIDFilter
from ai.backend.manager.api.gql.common.types import (
    SessionResultGQL,
    SessionTypeGQL,
)
from ai.backend.manager.api.gql.deployment.types.revision import EnvironmentVariablesGQL
from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL
from ai.backend.manager.api.gql.image.types import ImageConnectionV2GQL
from ai.backend.manager.api.gql.kernel.types import KernelConnectionV2GQL, ResourceAllocationGQL
from ai.backend.manager.api.gql.project_v2.types.node import ProjectV2GQL
from ai.backend.manager.api.gql.resource_group.resolver import ResourceGroupConnection
from ai.backend.manager.api.gql.resource_group.types import ResourceGroupGQL
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy
from ai.backend.manager.api.gql.user_v2.types.node import UserV2GQL
from ai.backend.manager.data.session.types import SessionInfo, SessionStatus
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder


@strawberry.enum(
    name="SessionStatus",
    description="Added in 26.2.0. Status of a session in its lifecycle.",
)
class SessionStatusGQL(StrEnum):
    """GraphQL enum for session status."""

    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    PREPARING = "PREPARING"
    PREPARED = "PREPARED"
    CREATING = "CREATING"
    RUNNING = "RUNNING"
    DEPRIORITIZING = "DEPRIORITIZING"
    TERMINATING = "TERMINATING"
    TERMINATED = "TERMINATED"
    CANCELLED = "CANCELLED"

    @classmethod
    def from_internal(cls, internal_status: SessionStatus) -> SessionStatusGQL:
        """Convert internal SessionStatus to GraphQL enum."""
        match internal_status:
            case SessionStatus.PENDING:
                return cls.PENDING
            case SessionStatus.SCHEDULED:
                return cls.SCHEDULED
            case SessionStatus.PREPARING | SessionStatus.PULLING:
                return cls.PREPARING
            case SessionStatus.PREPARED:
                return cls.PREPARED
            case SessionStatus.CREATING:
                return cls.CREATING
            case SessionStatus.RUNNING:
                return cls.RUNNING
            case SessionStatus.DEPRIORITIZING:
                return cls.DEPRIORITIZING
            case SessionStatus.TERMINATING:
                return cls.TERMINATING
            case SessionStatus.TERMINATED:
                return cls.TERMINATED
            case SessionStatus.CANCELLED:
                return cls.CANCELLED
            case _:
                # RESTARTING, RUNNING_DEGRADED, ERROR are not exposed via GQL
                return cls.CANCELLED

    def to_internal(self) -> SessionStatus:
        """Convert GraphQL enum to internal SessionStatus."""
        match self:
            case SessionStatusGQL.PENDING:
                return SessionStatus.PENDING
            case SessionStatusGQL.SCHEDULED:
                return SessionStatus.SCHEDULED
            case SessionStatusGQL.PREPARING:
                return SessionStatus.PREPARING
            case SessionStatusGQL.PREPARED:
                return SessionStatus.PREPARED
            case SessionStatusGQL.CREATING:
                return SessionStatus.CREATING
            case SessionStatusGQL.RUNNING:
                return SessionStatus.RUNNING
            case SessionStatusGQL.DEPRIORITIZING:
                return SessionStatus.DEPRIORITIZING
            case SessionStatusGQL.TERMINATING:
                return SessionStatus.TERMINATING
            case SessionStatusGQL.TERMINATED:
                return SessionStatus.TERMINATED
            case SessionStatusGQL.CANCELLED:
                return SessionStatus.CANCELLED


# ========== Order and Filter Types ==========


@strawberry.enum(
    name="SessionOrderField",
    description="Added in 26.2.0. Fields available for ordering sessions.",
)
class SessionOrderFieldGQL(StrEnum):
    CREATED_AT = "created_at"
    TERMINATED_AT = "terminated_at"
    STATUS = "status"
    ID = "id"
    NAME = "name"


@strawberry.input(
    name="SessionStatusFilter", description="Added in 26.2.0. Filter for session status."
)
class SessionStatusFilterGQL:
    in_: list[SessionStatusGQL] | None = strawberry.field(name="in", default=None)
    not_in: list[SessionStatusGQL] | None = None

    def build_condition(self) -> QueryCondition | None:
        raise NotImplementedError


@strawberry.input(
    name="SessionFilter", description="Added in 26.2.0. Filter criteria for querying sessions."
)
class SessionFilterGQL(GQLFilter):
    id: UUIDFilter | None = None
    status: SessionStatusFilterGQL | None = None
    name: str | None = None
    domain_name: str | None = None
    group_id: UUIDFilter | None = None
    user_uuid: UUIDFilter | None = None

    def build_conditions(self) -> list[QueryCondition]:
        raise NotImplementedError


@strawberry.input(
    name="SessionOrderBy", description="Added in 26.2.0. Ordering specification for sessions."
)
class SessionOrderByGQL(GQLOrderBy):
    field: SessionOrderFieldGQL
    direction: OrderDirection = OrderDirection.DESC

    def to_query_order(self) -> QueryOrder:
        raise NotImplementedError


# ========== Session Info Sub-Types ==========


@strawberry.type(
    name="SessionIdentityInfo",
    description="Added in 26.2.0. Basic identity information for a session.",
)
class SessionIdentityInfoGQL:
    id: ID = strawberry.field(description="Unique identifier of the session.")
    creation_id: str = strawberry.field(
        description="Server-generated unique token for tracking session creation."
    )
    name: str = strawberry.field(description="Human-readable name of the session.")
    session_type: SessionTypeGQL = strawberry.field(
        description="Type of the session (interactive, batch, inference)."
    )


@strawberry.type(
    name="SessionMetadataInfo",
    description="Added in 26.2.0. Metadata information for a session.",
)
class SessionMetadataInfoGQL:
    name: str = strawberry.field(description="Human-readable name of the session.")
    access_key: str = strawberry.field(description="Access key used to create this session.")
    cluster_mode: str = strawberry.field(
        description="Cluster mode for distributed sessions (single-node, multi-node)."
    )
    cluster_size: int = strawberry.field(description="Number of nodes in the cluster.")
    session_type: SessionTypeGQL = strawberry.field(
        description="Type of the session (interactive, batch, inference)."
    )
    priority: int = strawberry.field(description="Scheduling priority of the session.")
    created_at: datetime | None = strawberry.field(
        description="Timestamp when the session was created."
    )
    tag: str | None = strawberry.field(description="Optional user-provided tag for the session.")


@strawberry.type(
    name="SessionResourceInfo",
    description="Added in 26.2.0. Resource allocation information for a session.",
)
class SessionResourceInfoGQL:
    allocation: ResourceAllocationGQL = strawberry.field(
        description="Resource allocation with requested and occupied slots."
    )
    resource_group_name: str | None = strawberry.field(
        description="The resource group (scaling group) this session is assigned to."
    )
    target_resource_group_names: list[str] | None = strawberry.field(
        description="Candidate resource group names considered during scheduling."
    )


@strawberry.type(
    name="SessionLifecycleInfo",
    description="Added in 26.2.0. Lifecycle status and timestamps for a session.",
)
class SessionLifecycleInfoGQL:
    status: SessionStatusGQL = strawberry.field(description="Current status of the session.")
    result: SessionResultGQL = strawberry.field(
        description="Result of the session execution (success, failure, etc.)."
    )
    created_at: datetime | None = strawberry.field(
        description="Timestamp when the session was created."
    )
    terminated_at: datetime | None = strawberry.field(
        description="Timestamp when the session was terminated. Null if still active."
    )
    starts_at: datetime | None = strawberry.field(
        description="Scheduled start time for the session, if applicable."
    )
    batch_timeout: int | None = strawberry.field(
        description="Batch execution timeout in seconds. Applicable to batch sessions."
    )


@strawberry.type(
    name="SessionRuntimeInfo",
    description="Added in 26.2.0. Runtime execution configuration for a session.",
)
class SessionRuntimeInfoGQL:
    environ: EnvironmentVariablesGQL | None = strawberry.field(
        description="Environment variables for the session."
    )
    bootstrap_script: str | None = strawberry.field(
        description="Bootstrap script to run before the main process."
    )
    startup_command: str | None = strawberry.field(
        description="Startup command to execute when the session starts."
    )
    callback_url: str | None = strawberry.field(
        description="URL to call back when the session completes (e.g., for batch sessions)."
    )


@strawberry.type(
    name="SessionNetworkInfo",
    description="Added in 26.2.0. Network configuration for a session.",
)
class SessionNetworkInfoGQL:
    use_host_network: bool = strawberry.field(
        description="Whether the session uses the host network directly."
    )
    network_type: str | None = strawberry.field(description="Type of network used by the session.")
    network_id: str | None = strawberry.field(description="ID of the network if applicable.")


# ========== Main Session Type ==========


@strawberry.type(
    name="SessionV2",
    description="Added in 26.2.0. Represents a compute session in Backend.AI.",
)
class SessionV2GQL(Node):
    """Session type representing a compute session."""

    id: NodeID[str]

    identity: SessionIdentityInfoGQL = strawberry.field(
        description="Basic identity information for the session."
    )
    metadata: SessionMetadataInfoGQL = strawberry.field(
        description="Metadata including domain, group, and user information."
    )
    resource: SessionResourceInfoGQL = strawberry.field(
        description="Resource allocation and cluster information."
    )
    lifecycle: SessionLifecycleInfoGQL = strawberry.field(
        description="Lifecycle status and timestamps."
    )
    runtime: SessionRuntimeInfoGQL = strawberry.field(
        description="Runtime execution configuration."
    )
    network: SessionNetworkInfoGQL = strawberry.field(description="Network configuration.")

    @strawberry.field(  # type: ignore[misc]
        description="Added in 26.2.0. The domain this session belongs to."
    )
    async def domain(self) -> DomainV2GQL | None:
        raise NotImplementedError

    @strawberry.field(  # type: ignore[misc]
        description="Added in 26.2.0. The user who owns this session."
    )
    async def user(self) -> UserV2GQL | None:
        raise NotImplementedError

    @strawberry.field(  # type: ignore[misc]
        description="Added in 26.2.0. The project this session belongs to."
    )
    async def project(self) -> ProjectV2GQL | None:
        raise NotImplementedError

    @strawberry.field(  # type: ignore[misc]
        description="Added in 26.2.0. The resource group this session is assigned to."
    )
    async def resource_group(self) -> ResourceGroupGQL | None:
        raise NotImplementedError

    @strawberry.field(  # type: ignore[misc]
        description="Added in 26.2.0. The candidate resource groups considered during scheduling."
    )
    async def target_resource_groups(self) -> ResourceGroupConnection | None:
        raise NotImplementedError

    @strawberry.field(  # type: ignore[misc]
        description="Added in 26.2.0. The images used by this session. Multiple images are possible in multi-kernel (cluster) sessions."
    )
    async def images(self) -> ImageConnectionV2GQL:
        raise NotImplementedError

    @strawberry.field(  # type: ignore[misc]
        description="Added in 26.2.0. The kernels belonging to this session."
    )
    async def kernels(self) -> KernelConnectionV2GQL:
        raise NotImplementedError

    # TODO: Add `vfolder_mounts` dynamic field (VFolderV2 connection type needed)

    @classmethod
    def from_session_info(cls, session_info: SessionInfo) -> Self:
        """Create SessionV2GQL from SessionInfo dataclass."""
        raise NotImplementedError


# ========== Connection Types ==========


SessionEdgeGQL = Edge[SessionV2GQL]


@strawberry.type(
    name="SessionConnectionV2",
    description="Added in 26.2.0. Connection type for paginated session results.",
)
class SessionConnectionV2GQL(Connection[SessionV2GQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
