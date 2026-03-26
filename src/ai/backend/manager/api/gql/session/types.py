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
    PydanticInputMixin,
    gql_added_field,
    gql_connection_type,
    gql_enum,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.deployment.types.revision import EnvironmentVariablesGQL
from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL
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
from ai.backend.manager.errors.user import UserNotFound


@gql_enum(
    BackendAIGQLMeta(added_version="26.3.0", description="Status of a session in its lifecycle."),
    name="SessionV2Status",
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


# ========== Order and Filter Types ==========


@gql_enum(
    BackendAIGQLMeta(added_version="26.3.0", description="Fields available for ordering sessions."),
    name="SessionV2OrderField",
)
class SessionV2OrderFieldGQL(StrEnum):
    CREATED_AT = "created_at"
    TERMINATED_AT = "terminated_at"
    STATUS = "status"
    ID = "id"
    NAME = "name"


@gql_pydantic_input(
    BackendAIGQLMeta(description="Filter for session status.", added_version="26.3.0"),
    name="SessionV2StatusFilter",
)
class SessionV2StatusFilterGQL(PydanticInputMixin[SessionStatusFilter]):
    in_: list[SessionV2StatusGQL] | None = gql_field(
        description="The in  field.", name="in", default=None
    )
    not_in: list[SessionV2StatusGQL] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter criteria for querying sessions.",
        added_version="26.3.0",
    ),
    name="SessionV2Filter",
)
class SessionV2FilterGQL(PydanticInputMixin[SessionFilter]):
    id: UUIDFilter | None = None
    status: SessionV2StatusFilterGQL | None = None
    name: StringFilter | None = None
    domain_name: StringFilter | None = None
    project_id: UUIDFilter | None = None
    user_uuid: UUIDFilter | None = None

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(description="Ordering specification for sessions.", added_version="26.3.0"),
    name="SessionV2OrderBy",
)
class SessionV2OrderByGQL(PydanticInputMixin[SessionOrder]):
    field: SessionV2OrderFieldGQL
    direction: OrderDirection = OrderDirection.DESC


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
    creation_id: str = gql_field(
        description="Server-generated unique token for tracking session creation."
    )
    name: str = gql_field(description="Human-readable name of the session.")
    session_type: SessionV2TypeGQL = gql_field(
        description="Type of the session (interactive, batch, inference)."
    )
    access_key: str = gql_field(description="Access key used to create this session.")
    cluster_mode: ClusterModeGQL = gql_field(
        description="Cluster mode for distributed sessions (single-node, multi-node)."
    )
    cluster_size: int = gql_field(description="Number of nodes in the cluster.")
    priority: int = gql_field(description="Scheduling priority of the session.")
    is_preemptible: bool = gql_field(
        description="Whether this session is eligible for preemption by higher-priority sessions."
    )
    tag: str | None = gql_field(description="Optional user-provided tag for the session.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Resource allocation information for a session.",
    ),
    model=SessionResourceInfoGQLDTO,
    name="SessionV2ResourceInfo",
)
class SessionV2ResourceInfoGQL:
    allocation: ResourceAllocationGQL = gql_field(
        description="Resource allocation with requested and occupied slots."
    )
    resource_group_name: str | None = gql_field(
        description="The resource group (scaling group) this session is assigned to."
    )
    target_resource_group_names: list[str] | None = gql_field(
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
    status: SessionV2StatusGQL = gql_field(description="Current status of the session.")
    result: SessionV2ResultGQL = gql_field(
        description="Result of the session execution (success, failure, etc.)."
    )
    created_at: datetime | None = gql_field(description="Timestamp when the session was created.")
    terminated_at: datetime | None = gql_field(
        description="Timestamp when the session was terminated. Null if still active."
    )
    starts_at: datetime | None = gql_field(
        description="Scheduled start time for the session, if applicable."
    )
    batch_timeout: int | None = gql_field(
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
    environ: EnvironmentVariablesGQL | None = gql_field(
        description="Environment variables for the session."
    )
    bootstrap_script: str | None = gql_field(
        description="Bootstrap script to run before the main process."
    )
    startup_command: str | None = gql_field(
        description="Startup command to execute when the session starts."
    )
    callback_url: str | None = gql_field(
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

    metadata: SessionV2MetadataInfoGQL = gql_field(
        description="Metadata including domain, project, and user information."
    )
    resource: SessionV2ResourceInfoGQL = gql_field(
        description="Resource allocation and cluster information."
    )
    lifecycle: SessionV2LifecycleInfoGQL = gql_field(description="Lifecycle status and timestamps.")
    runtime: SessionV2RuntimeInfoGQL = gql_field(description="Runtime execution configuration.")
    network: SessionV2NetworkInfoGQL = gql_field(description="Network configuration.")

    @gql_added_field(
        BackendAIGQLMeta(added_version="26.3.0", description="The domain this session belongs to.")
    )  # type: ignore[misc]
    async def domain(self, info: Info[StrawberryGQLContext]) -> DomainV2GQL | None:
        return await info.context.data_loaders.domain_loader.load(self.domain_name)

    @gql_added_field(
        BackendAIGQLMeta(added_version="26.3.0", description="The user who owns this session.")
    )  # type: ignore[misc]
    async def user(self, info: Info[StrawberryGQLContext]) -> UserV2GQL | None:
        user_data = await info.context.data_loaders.user_loader.load(UUID(str(self.user_id)))
        if user_data is None:
            return None
        return user_data

    @gql_added_field(
        BackendAIGQLMeta(added_version="26.3.0", description="The project this session belongs to.")
    )  # type: ignore[misc]
    async def project(self, info: Info[StrawberryGQLContext]) -> ProjectV2GQL | None:
        project_data = await info.context.data_loaders.project_loader.load(
            UUID(str(self.project_id))
        )
        if project_data is None:
            return None
        return project_data

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.3.0", description="The resource group this session is assigned to."
        )
    )  # type: ignore[misc]
    async def resource_group(self, info: Info[StrawberryGQLContext]) -> ResourceGroupGQL | None:
        if self.resource.resource_group_name is None:
            return None
        resource_group_data = await info.context.data_loaders.resource_group_loader.load(
            self.resource.resource_group_name
        )
        if resource_group_data is None:
            return None
        return resource_group_data

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.3.0",
            description="The candidate resource groups considered during scheduling.",
        )
    )  # type: ignore[misc]
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

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.3.0",
            description="The images used by this session. Multiple images are possible in multi-kernel (cluster) sessions.",
        )
    )  # type: ignore[misc]
    async def images(self) -> ImageV2ConnectionGQL:
        raise NotImplementedError

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.3.0", description="The kernels belonging to this session."
        )
    )  # type: ignore[misc]
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
