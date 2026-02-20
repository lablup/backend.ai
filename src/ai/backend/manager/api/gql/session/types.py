"""GraphQL types for session management."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import Any, Self
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.common.types import SessionId
from ai.backend.manager.api.gql.base import OrderDirection, StringMatchSpec, UUIDFilter
from ai.backend.manager.api.gql.common.types import (
    ClusterModeGQL,
    SessionV2ResultGQL,
    SessionV2TypeGQL,
)
from ai.backend.manager.api.gql.deployment.types.revision import (
    EnvironmentVariableEntryGQL,
    EnvironmentVariablesGQL,
)
from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL
from ai.backend.manager.api.gql.fair_share.types.common import ResourceSlotGQL
from ai.backend.manager.api.gql.image.types import ImageV2ConnectionGQL
from ai.backend.manager.api.gql.kernel.types import KernelV2ConnectionGQL, ResourceAllocationGQL
from ai.backend.manager.api.gql.project_v2.types.node import ProjectV2GQL
from ai.backend.manager.api.gql.resource_group.resolver import ResourceGroupConnection
from ai.backend.manager.api.gql.resource_group.types import ResourceGroupGQL
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext
from ai.backend.manager.api.gql.user.types.node import UserV2GQL
from ai.backend.manager.data.session.types import SessionData, SessionStatus
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder
from ai.backend.manager.repositories.scheduler.options import SessionConditions, SessionOrders


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
        if self.in_:
            return SessionConditions.by_status_in([s.to_internal() for s in self.in_])
        if self.not_in:
            return SessionConditions.by_status_not_in([s.to_internal() for s in self.not_in])
        return None


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
        conditions: list[QueryCondition] = []
        if self.id:
            condition = self.id.build_query_condition(
                SessionConditions.by_id_filter_equals,
                SessionConditions.by_id_filter_in,
            )
            if condition:
                conditions.append(condition)
        if self.status:
            condition = self.status.build_condition()
            if condition:
                conditions.append(condition)
        if self.name is not None:
            conditions.append(
                SessionConditions.by_name_equals(
                    StringMatchSpec(self.name, case_insensitive=False, negated=False)
                )
            )
        if self.domain_name is not None:
            conditions.append(SessionConditions.by_domain_name(self.domain_name))
        if self.project_id:
            condition = self.project_id.build_query_condition(
                SessionConditions.by_group_id_filter_equals,
                SessionConditions.by_group_id_filter_in,
            )
            if condition:
                conditions.append(condition)
        if self.user_uuid:
            condition = self.user_uuid.build_query_condition(
                SessionConditions.by_user_uuid_filter_equals,
                SessionConditions.by_user_uuid_filter_in,
            )
            if condition:
                conditions.append(condition)
        return conditions


@strawberry.input(
    name="SessionV2OrderBy", description="Added in 26.3.0. Ordering specification for sessions."
)
class SessionV2OrderByGQL(GQLOrderBy):
    field: SessionV2OrderFieldGQL
    direction: OrderDirection = OrderDirection.DESC

    def to_query_order(self) -> QueryOrder:
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case SessionV2OrderFieldGQL.CREATED_AT:
                return SessionOrders.created_at(ascending)
            case SessionV2OrderFieldGQL.TERMINATED_AT:
                return SessionOrders.terminated_at(ascending)
            case SessionV2OrderFieldGQL.STATUS:
                return SessionOrders.status(ascending)
            case SessionV2OrderFieldGQL.ID:
                return SessionOrders.id(ascending)
            case SessionV2OrderFieldGQL.NAME:
                return SessionOrders.name(ascending)
            case _:
                raise ValueError(f"Unhandled SessionV2OrderFieldGQL value: {self.field!r}")


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

    # Private fields for dynamic resolvers
    _domain_name: strawberry.Private[str]
    _user_uuid: strawberry.Private[UUID]
    _group_id: strawberry.Private[UUID]

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
    async def domain(self, info: Info[StrawberryGQLContext]) -> DomainV2GQL | None:
        domain_data = await info.context.data_loaders.domain_loader.load(self._domain_name)
        if domain_data is None:
            return None
        return DomainV2GQL.from_data(domain_data)

    @strawberry.field(  # type: ignore[misc]
        description="Added in 26.3.0. The user who owns this session."
    )
    async def user(self, info: Info[StrawberryGQLContext]) -> UserV2GQL | None:
        user_data = await info.context.data_loaders.user_loader.load(self._user_uuid)
        if user_data is None:
            return None
        return UserV2GQL.from_data(user_data)

    @strawberry.field(  # type: ignore[misc]
        description="Added in 26.3.0. The project this session belongs to."
    )
    async def project(self, info: Info[StrawberryGQLContext]) -> ProjectV2GQL | None:
        project_data = await info.context.data_loaders.project_loader.load(self._group_id)
        if project_data is None:
            return None
        return ProjectV2GQL.from_data(project_data)

    @strawberry.field(  # type: ignore[misc]
        description="Added in 26.3.0. The resource group this session is assigned to."
    )
    async def resource_group(self, info: Info[StrawberryGQLContext]) -> ResourceGroupGQL | None:
        if self.resource.resource_group_name is None:
            return None
        resource_group_data = await info.context.data_loaders.resource_group_loader.load(
            self.resource.resource_group_name
        )
        if resource_group_data is None:
            return None
        return ResourceGroupGQL.from_dataclass(resource_group_data)

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
        results = await info.context.data_loaders.session_loader.load_many([
            SessionId(UUID(nid)) for nid in node_ids
        ])
        return [cls.from_data(data) if data is not None else None for data in results]

    @classmethod
    def from_data(cls, data: SessionData) -> Self:
        """Create SessionV2GQL from SessionData dataclass."""
        requested_slots = (
            ResourceSlotGQL.from_resource_slot(data.requested_slots)
            if data.requested_slots
            else ResourceSlotGQL(entries=[])
        )
        occupying_slots = (
            ResourceSlotGQL.from_resource_slot(data.occupying_slots)
            if data.occupying_slots
            else None
        )

        environ_gql: EnvironmentVariablesGQL | None = None
        if data.environ:
            environ_gql = EnvironmentVariablesGQL(
                entries=[
                    EnvironmentVariableEntryGQL(name=k, value=str(v))
                    for k, v in data.environ.items()
                ]
            )

        return cls(
            id=ID(str(data.id)),
            _domain_name=data.domain_name,
            _user_uuid=data.user_uuid,
            _group_id=data.group_id,
            metadata=SessionV2MetadataInfoGQL(
                creation_id=data.creation_id or "",
                name=data.name or "",
                session_type=SessionV2TypeGQL.from_internal(data.session_type),
                access_key=str(data.access_key) if data.access_key else "",
                cluster_mode=ClusterModeGQL.from_internal(data.cluster_mode),
                cluster_size=data.cluster_size,
                priority=data.priority,
                tag=data.tag,
            ),
            resource=SessionV2ResourceInfoGQL(
                allocation=ResourceAllocationGQL(
                    requested=requested_slots,
                    used=occupying_slots,
                ),
                resource_group_name=data.scaling_group_name,
                target_resource_group_names=data.target_sgroup_names,
            ),
            lifecycle=SessionV2LifecycleInfoGQL(
                status=SessionV2StatusGQL.from_internal(data.status),
                result=SessionV2ResultGQL.from_internal(data.result),
                created_at=data.created_at,
                terminated_at=data.terminated_at,
                starts_at=data.starts_at,
                batch_timeout=data.batch_timeout,
            ),
            runtime=SessionV2RuntimeInfoGQL(
                environ=environ_gql,
                bootstrap_script=data.bootstrap_script,
                startup_command=data.startup_command,
                callback_url=data.callback_url,
            ),
            network=SessionV2NetworkInfoGQL(
                use_host_network=data.use_host_network,
                network_type=str(data.network_type) if data.network_type else None,
                network_id=data.network_id,
            ),
        )


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
