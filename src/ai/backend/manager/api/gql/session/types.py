"""GraphQL types for session management."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import Any, Self

import strawberry
from strawberry import Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.manager.api.gql.base import OrderDirection, UUIDFilter
from ai.backend.manager.api.gql.common.types import (
    ClusterModeGQL,
    SessionV2ResultGQL,
    SessionV2TypeGQL,
)
from ai.backend.manager.api.gql.deployment.types.revision import EnvironmentVariablesGQL
from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL
from ai.backend.manager.api.gql.image.types import ImageV2ConnectionGQL
from ai.backend.manager.api.gql.kernel.types import KernelV2ConnectionGQL, ResourceAllocationGQL
from ai.backend.manager.api.gql.project_v2.types.node import ProjectV2GQL
from ai.backend.manager.api.gql.resource_group.resolver import ResourceGroupConnection
from ai.backend.manager.api.gql.resource_group.types import ResourceGroupGQL
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext
from ai.backend.manager.api.gql.user.types.node import UserV2GQL
from ai.backend.manager.data.session.types import SessionInfo, SessionStatus
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder


@strawberry.enum(
    name="SessionV2Status",
    description="Added in 26.3.0. Status of a session in its lifecycle.",
)
class SessionV2StatusGQL(StrEnum):
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
    def from_internal(cls, internal_status: SessionStatus) -> SessionV2StatusGQL:
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
            case SessionV2StatusGQL.PENDING:
                return SessionStatus.PENDING
            case SessionV2StatusGQL.SCHEDULED:
                return SessionStatus.SCHEDULED
            case SessionV2StatusGQL.PREPARING:
                return SessionStatus.PREPARING
            case SessionV2StatusGQL.PREPARED:
                return SessionStatus.PREPARED
            case SessionV2StatusGQL.CREATING:
                return SessionStatus.CREATING
            case SessionV2StatusGQL.RUNNING:
                return SessionStatus.RUNNING
            case SessionV2StatusGQL.DEPRIORITIZING:
                return SessionStatus.DEPRIORITIZING
            case SessionV2StatusGQL.TERMINATING:
                return SessionStatus.TERMINATING
            case SessionV2StatusGQL.TERMINATED:
                return SessionStatus.TERMINATED
            case SessionV2StatusGQL.CANCELLED:
                return SessionStatus.CANCELLED


# ========== Order and Filter Types ==========


@strawberry.enum(
    name="SessionV2OrderField",
    description="Added in 26.3.0. Fields available for ordering sessions.",
)
class SessionV2OrderFieldGQL(StrEnum):
    CREATED_AT = "created_at"
    TERMINATED_AT = "terminated_at"
    STATUS = "status"
    ID = "id"
    NAME = "name"


@strawberry.input(
    name="SessionV2StatusFilter", description="Added in 26.3.0. Filter for session status."
)
class SessionV2StatusFilterGQL:
    in_: list[SessionV2StatusGQL] | None = strawberry.field(name="in", default=None)
    not_in: list[SessionV2StatusGQL] | None = None

    def build_condition(self) -> QueryCondition | None:
        raise NotImplementedError


@strawberry.input(
    name="SessionV2Filter", description="Added in 26.3.0. Filter criteria for querying sessions."
)
class SessionV2FilterGQL(GQLFilter):
    id: UUIDFilter | None = None
    status: SessionV2StatusFilterGQL | None = None
    name: str | None = None
    domain_name: str | None = None
    project_id: UUIDFilter | None = None
    user_uuid: UUIDFilter | None = None

    def build_conditions(self) -> list[QueryCondition]:
        raise NotImplementedError


@strawberry.input(
    name="SessionV2OrderBy", description="Added in 26.3.0. Ordering specification for sessions."
)
class SessionV2OrderByGQL(GQLOrderBy):
    field: SessionV2OrderFieldGQL
    direction: OrderDirection = OrderDirection.DESC

    def to_query_order(self) -> QueryOrder:
        raise NotImplementedError


# ========== Session Info Sub-Types ==========


@strawberry.type(
    name="SessionV2MetadataInfo",
    description="Added in 26.3.0. Metadata information for a session.",
)
class SessionV2MetadataInfoGQL:
    creation_id: str = strawberry.field(
        description="Server-generated unique token for tracking session creation."
    )
    name: str = strawberry.field(description="Human-readable name of the session.")
    session_type: SessionV2TypeGQL = strawberry.field(
        description="Type of the session (interactive, batch, inference)."
    )
    access_key: str = strawberry.field(description="Access key used to create this session.")
    cluster_mode: ClusterModeGQL = strawberry.field(
        description="Cluster mode for distributed sessions (single-node, multi-node)."
    )
    cluster_size: int = strawberry.field(description="Number of nodes in the cluster.")
    priority: int = strawberry.field(description="Scheduling priority of the session.")
    tag: str | None = strawberry.field(description="Optional user-provided tag for the session.")


@strawberry.type(
    name="SessionV2ResourceInfo",
    description="Added in 26.3.0. Resource allocation information for a session.",
)
class SessionV2ResourceInfoGQL:
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
    name="SessionV2LifecycleInfo",
    description="Added in 26.3.0. Lifecycle status and timestamps for a session.",
)
class SessionV2LifecycleInfoGQL:
    status: SessionV2StatusGQL = strawberry.field(description="Current status of the session.")
    result: SessionV2ResultGQL = strawberry.field(
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
    name="SessionV2RuntimeInfo",
    description="Added in 26.3.0. Runtime execution configuration for a session.",
)
class SessionV2RuntimeInfoGQL:
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
    name="SessionV2NetworkInfo",
    description="Added in 26.3.0. Network configuration for a session.",
)
class SessionV2NetworkInfoGQL:
    use_host_network: bool = strawberry.field(
        description="Whether the session uses the host network directly."
    )
    network_type: str | None = strawberry.field(description="Type of network used by the session.")
    network_id: str | None = strawberry.field(description="ID of the network if applicable.")


# ========== Main Session Type ==========


@strawberry.type(
    name="SessionV2",
    description="Added in 26.3.0. Represents a compute session in Backend.AI.",
)
class SessionV2GQL(Node):
    """Session type representing a compute session."""

    id: NodeID[str]

    metadata: SessionV2MetadataInfoGQL = strawberry.field(
        description="Metadata including domain, project, and user information."
    )
    resource: SessionV2ResourceInfoGQL = strawberry.field(
        description="Resource allocation and cluster information."
    )
    lifecycle: SessionV2LifecycleInfoGQL = strawberry.field(
        description="Lifecycle status and timestamps."
    )
    runtime: SessionV2RuntimeInfoGQL = strawberry.field(
        description="Runtime execution configuration."
    )
    network: SessionV2NetworkInfoGQL = strawberry.field(description="Network configuration.")

    @strawberry.field(  # type: ignore[misc]
        description="Added in 26.3.0. The domain this session belongs to."
    )
    async def domain(self) -> DomainV2GQL | None:
        raise NotImplementedError

    @strawberry.field(  # type: ignore[misc]
        description="Added in 26.3.0. The user who owns this session."
    )
    async def user(self) -> UserV2GQL | None:
        raise NotImplementedError

    @strawberry.field(  # type: ignore[misc]
        description="Added in 26.3.0. The project this session belongs to."
    )
    async def project(self) -> ProjectV2GQL | None:
        raise NotImplementedError

    @strawberry.field(  # type: ignore[misc]
        description="Added in 26.3.0. The resource group this session is assigned to."
    )
    async def resource_group(self) -> ResourceGroupGQL | None:
        raise NotImplementedError

    @strawberry.field(  # type: ignore[misc]
        description="Added in 26.3.0. The candidate resource groups considered during scheduling."
    )
    async def target_resource_groups(self) -> ResourceGroupConnection | None:
        raise NotImplementedError

    @strawberry.field(  # type: ignore[misc]
        description="Added in 26.3.0. The images used by this session. Multiple images are possible in multi-kernel (cluster) sessions."
    )
    async def images(self) -> ImageV2ConnectionGQL:
        raise NotImplementedError

    @strawberry.field(  # type: ignore[misc]
        description="Added in 26.3.0. The kernels belonging to this session."
    )
    async def kernels(self) -> KernelV2ConnectionGQL:
        raise NotImplementedError

    # TODO: Add `vfolder_mounts` dynamic field (VFolderV2 connection type needed)

    @classmethod
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        raise NotImplementedError

    @classmethod
    def from_session_info(cls, session_info: SessionInfo) -> Self:
        """Create SessionV2GQL from SessionInfo dataclass."""
        raise NotImplementedError


# ========== Connection Types ==========


SessionV2EdgeGQL = Edge[SessionV2GQL]


@strawberry.type(
    name="SessionV2Connection",
    description="Added in 26.3.0. Connection type for paginated session results.",
)
class SessionV2ConnectionGQL(Connection[SessionV2GQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
