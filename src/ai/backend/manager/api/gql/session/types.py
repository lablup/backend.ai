"""GraphQL types for session management."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import Any, Self, cast
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.v2.kernel.request import AdminSearchKernelsInput
from ai.backend.common.dto.manager.v2.session.request import SessionFilter, SessionOrder
from ai.backend.common.dto.manager.v2.session.response import (
    SessionLifecycleInfoGQLDTO,
    SessionMetadataInfoGQLDTO,
    SessionNetworkInfo,
    SessionNode,
    SessionResourceInfoGQLDTO,
    SessionRuntimeInfoGQLDTO,
)
from ai.backend.common.dto.manager.v2.session.types import (
    OrderDirection as OrderDirectionDTO,
)
from ai.backend.common.dto.manager.v2.session.types import (
    SessionOrderField,
    SessionStatusEnum,
    SessionStatusFilter,
)
from ai.backend.common.types import SessionId
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter, UUIDFilter, encode_cursor
from ai.backend.manager.api.gql.common.types import (
    ClusterModeGQL,
    SessionV2ResultGQL,
    SessionV2TypeGQL,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_connection_type,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.deployment.types.revision import (
    EnvironmentVariableEntryGQL,
    EnvironmentVariablesGQL,
)
from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL
from ai.backend.manager.api.gql.fair_share.types.common import ResourceSlotGQL
from ai.backend.manager.api.gql.image.types import ImageV2ConnectionGQL
from ai.backend.manager.api.gql.kernel.types import (
    KernelV2ConnectionGQL,
    KernelV2EdgeGQL,
    KernelV2GQL,
    ResourceAllocationGQL,
)
from ai.backend.manager.api.gql.project_v2.types.node import ProjectV2GQL
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.resource_group.resolver import (
    ResourceGroupConnection,
    ResourceGroupEdge,
)
from ai.backend.manager.api.gql.resource_group.types import ResourceGroupGQL
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.user.types.node import UserV2GQL
from ai.backend.manager.data.session.types import SessionData, SessionStatus
from ai.backend.manager.errors.user import UserNotFound


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


@gql_pydantic_input(
    BackendAIGQLMeta(description="Filter for session status.", added_version="26.3.0"),
    model=SessionStatusFilter,
    name="SessionV2StatusFilter",
)
class SessionV2StatusFilterGQL:
    in_: list[SessionV2StatusGQL] | None = strawberry.field(name="in", default=None)
    not_in: list[SessionV2StatusGQL] | None = None

    def to_pydantic(self) -> SessionStatusFilter:
        return SessionStatusFilter(
            in_=[SessionStatusEnum(s) for s in self.in_] if self.in_ else None,
            not_in=[SessionStatusEnum(s) for s in self.not_in] if self.not_in else None,
        )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter criteria for querying sessions.",
        added_version="26.3.0",
    ),
    model=SessionFilter,
    name="SessionV2Filter",
)
class SessionV2FilterGQL:
    id: UUIDFilter | None = None
    status: SessionV2StatusFilterGQL | None = None
    name: StringFilter | None = None
    domain_name: StringFilter | None = None
    project_id: UUIDFilter | None = None
    user_uuid: UUIDFilter | None = None

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None

    def to_pydantic(self) -> SessionFilter:
        return SessionFilter(
            id=self.id.to_pydantic() if self.id else None,
            status=self.status.to_pydantic() if self.status else None,
            name=self.name.to_pydantic() if self.name else None,
            domain_name=self.domain_name.to_pydantic() if self.domain_name else None,
            project_id=self.project_id.to_pydantic() if self.project_id else None,
            user_uuid=self.user_uuid.to_pydantic() if self.user_uuid else None,
            AND=[f.to_pydantic() for f in self.AND] if self.AND else None,
            OR=[f.to_pydantic() for f in self.OR] if self.OR else None,
            NOT=[f.to_pydantic() for f in self.NOT] if self.NOT else None,
        )


@gql_pydantic_input(
    BackendAIGQLMeta(description="Ordering specification for sessions.", added_version="26.3.0"),
    model=SessionOrder,
    name="SessionV2OrderBy",
)
class SessionV2OrderByGQL:
    field: SessionV2OrderFieldGQL
    direction: OrderDirection = OrderDirection.DESC

    def to_pydantic(self) -> SessionOrder:
        ascending = self.direction == OrderDirection.ASC
        direction = OrderDirectionDTO.ASC if ascending else OrderDirectionDTO.DESC
        match self.field:
            case SessionV2OrderFieldGQL.CREATED_AT:
                return SessionOrder(field=SessionOrderField.CREATED_AT, direction=direction)
            case SessionV2OrderFieldGQL.TERMINATED_AT:
                return SessionOrder(field=SessionOrderField.TERMINATED_AT, direction=direction)
            case SessionV2OrderFieldGQL.STATUS:
                return SessionOrder(field=SessionOrderField.STATUS, direction=direction)
            case SessionV2OrderFieldGQL.ID:
                return SessionOrder(field=SessionOrderField.ID, direction=direction)
            case SessionV2OrderFieldGQL.NAME:
                return SessionOrder(field=SessionOrderField.NAME, direction=direction)


# ========== Session Info Sub-Types ==========


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Metadata information for a session.",
    ),
    model=SessionMetadataInfoGQLDTO,
    name="SessionV2MetadataInfo",
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
    is_preemptible: bool = strawberry.field(
        description="Whether this session is eligible for preemption by higher-priority sessions."
    )
    tag: str | None = strawberry.field(description="Optional user-provided tag for the session.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Resource allocation information for a session.",
    ),
    model=SessionResourceInfoGQLDTO,
    name="SessionV2ResourceInfo",
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


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Lifecycle status and timestamps for a session.",
    ),
    model=SessionLifecycleInfoGQLDTO,
    name="SessionV2LifecycleInfo",
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


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Runtime execution configuration for a session.",
    ),
    model=SessionRuntimeInfoGQLDTO,
    name="SessionV2RuntimeInfo",
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


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Network configuration for a session.",
    ),
    model=SessionNetworkInfo,
    name="SessionV2NetworkInfo",
)
class SessionV2NetworkInfoGQL:
    use_host_network: strawberry.auto
    network_type: strawberry.auto
    network_id: strawberry.auto


# ========== Main Session Type ==========


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Represents a compute session in Backend.AI.",
    ),
    name="SessionV2",
)
class SessionV2GQL(PydanticNodeMixin[SessionNode]):
    """Session type representing a compute session."""

    id: NodeID[str]

    # Fields used as keys for dynamic resolvers
    domain_name: str
    user_id: ID
    project_id: ID

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
        return await info.context.data_loaders.domain_loader.load(self.domain_name)

    @strawberry.field(  # type: ignore[misc]
        description="Added in 26.3.0. The user who owns this session."
    )
    async def user(self, info: Info[StrawberryGQLContext]) -> UserV2GQL | None:
        user_data = await info.context.data_loaders.user_loader.load(UUID(str(self.user_id)))
        if user_data is None:
            return None
        return user_data

    @strawberry.field(  # type: ignore[misc]
        description="Added in 26.3.0. The project this session belongs to."
    )
    async def project(self, info: Info[StrawberryGQLContext]) -> ProjectV2GQL | None:
        project_data = await info.context.data_loaders.project_loader.load(
            UUID(str(self.project_id))
        )
        if project_data is None:
            return None
        return project_data

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
        return resource_group_data

    @strawberry.field(  # type: ignore[misc]
        description="Added in 26.3.0. The candidate resource groups considered during scheduling."
    )
    async def target_resource_groups(
        self, info: Info[StrawberryGQLContext]
    ) -> ResourceGroupConnection | None:
        names = self.resource.target_resource_group_names
        if not names:
            return None
        results = await info.context.data_loaders.resource_group_loader.load_many(names)
        nodes = [data for data in results if data is not None]
        edges = [ResourceGroupEdge(node=node, cursor=encode_cursor(node.id)) for node in nodes]
        return ResourceGroupConnection(
            edges=edges,
            page_info=strawberry.relay.PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
            count=len(nodes),
        )

    @strawberry.field(  # type: ignore[misc]
        description="Added in 26.3.0. The images used by this session. Multiple images are possible in multi-kernel (cluster) sessions."
    )
    async def images(self) -> ImageV2ConnectionGQL:
        raise NotImplementedError

    @strawberry.field(  # type: ignore[misc]
        description="Added in 26.3.0. The kernels belonging to this session."
    )
    async def kernels(self, info: Info[StrawberryGQLContext]) -> KernelV2ConnectionGQL:
        user = current_user()
        if user is None:
            raise UserNotFound("User not found in context")

        session_id = SessionId(UUID(str(self.id)))
        payload = await info.context.adapters.session.search_kernels_by_session(
            session_id, AdminSearchKernelsInput()
        )
        nodes = [KernelV2GQL.from_pydantic(kernel) for kernel in payload.items]
        edges = [KernelV2EdgeGQL(node=node, cursor=encode_cursor(node.id)) for node in nodes]
        return KernelV2ConnectionGQL(
            edges=edges,
            page_info=strawberry.relay.PageInfo(
                has_next_page=payload.has_next_page,
                has_previous_page=payload.has_previous_page,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
            count=payload.total_count,
        )

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
        return cast(list[Self | None], results)

    @classmethod
    def from_data(cls, data: SessionData) -> Self:
        """Create SessionV2GQL from SessionData dataclass."""
        requested_slots = ResourceSlotGQL.from_resource_slot(data.requested_slots)
        occupying_slots = ResourceSlotGQL.from_resource_slot(data.occupying_slots)

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
            domain_name=data.domain_name,
            user_id=ID(str(data.user_uuid)),
            project_id=ID(str(data.group_id)),
            metadata=SessionV2MetadataInfoGQL(
                creation_id=data.creation_id or "",
                name=data.name or "",
                session_type=SessionV2TypeGQL.from_internal(data.session_type),
                access_key=str(data.access_key) if data.access_key else "",
                cluster_mode=ClusterModeGQL.from_internal(data.cluster_mode),
                cluster_size=data.cluster_size,
                priority=data.priority,
                is_preemptible=data.is_preemptible,
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

    @classmethod
    def from_pydantic(
        cls,
        dto: SessionNode,
        extra: dict[str, Any] | None = None,
        *,
        id_field: str = "id",
    ) -> Self:
        """Create SessionV2GQL from SessionNode DTO (adapter search results)."""
        from ai.backend.common.types import ClusterMode, ResourceSlot, SessionResult, SessionTypes
        from ai.backend.manager.data.session.types import SessionStatus as SessionStatusInternal

        requested_slots = ResourceSlotGQL.from_resource_slot(
            ResourceSlot.from_json(dto.resource.requested_slots)
            if dto.resource.requested_slots
            else {}
        )
        occupying_slots = ResourceSlotGQL.from_resource_slot(
            ResourceSlot.from_json(dto.resource.occupying_slots)
            if dto.resource.occupying_slots
            else {}
        )

        status = SessionV2StatusGQL.from_internal(SessionStatusInternal(dto.lifecycle.status))
        result = SessionV2ResultGQL.from_internal(SessionResult(dto.lifecycle.result))

        environ_gql: EnvironmentVariablesGQL | None = None
        if dto.runtime.environ:
            environ_gql = EnvironmentVariablesGQL(
                entries=[
                    EnvironmentVariableEntryGQL(name=k, value=v)
                    for k, v in dto.runtime.environ.items()
                ]
            )

        return cls(
            id=ID(str(dto.id)),
            domain_name=dto.domain_name,
            user_id=ID(str(dto.user_uuid)),
            project_id=ID(str(dto.group_id)),
            metadata=SessionV2MetadataInfoGQL(
                creation_id=dto.metadata.creation_id or "",
                name=dto.metadata.name or "",
                session_type=SessionV2TypeGQL.from_internal(
                    SessionTypes(dto.metadata.session_type)
                ),
                access_key=dto.metadata.access_key or "",
                cluster_mode=ClusterModeGQL.from_internal(ClusterMode(dto.metadata.cluster_mode)),
                cluster_size=dto.metadata.cluster_size,
                priority=dto.metadata.priority,
                is_preemptible=dto.metadata.is_preemptible,
                tag=dto.metadata.tag,
            ),
            resource=SessionV2ResourceInfoGQL(
                allocation=ResourceAllocationGQL(
                    requested=requested_slots,
                    used=occupying_slots,
                ),
                resource_group_name=dto.resource.scaling_group_name,
                target_resource_group_names=dto.resource.target_sgroup_names,
            ),
            lifecycle=SessionV2LifecycleInfoGQL(
                status=status,
                result=result,
                created_at=dto.lifecycle.created_at,
                terminated_at=dto.lifecycle.terminated_at,
                starts_at=dto.lifecycle.starts_at,
                batch_timeout=dto.lifecycle.batch_timeout,
            ),
            runtime=SessionV2RuntimeInfoGQL(
                environ=environ_gql,
                bootstrap_script=dto.runtime.bootstrap_script,
                startup_command=dto.runtime.startup_command,
                callback_url=dto.runtime.callback_url,
            ),
            network=SessionV2NetworkInfoGQL(
                use_host_network=dto.network.use_host_network,
                network_type=dto.network.network_type,
                network_id=dto.network.network_id,
            ),
        )


# ========== Connection Types ==========


SessionV2EdgeGQL = Edge[SessionV2GQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Connection type for paginated session results.",
    ),
    name="SessionV2Connection",
)
class SessionV2ConnectionGQL(Connection[SessionV2GQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
