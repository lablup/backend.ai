"""GraphQL types for kernel management."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Any, Self, cast
from uuid import UUID

import strawberry
from strawberry import Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.kernel.request import KernelFilter, KernelOrder
from ai.backend.common.dto.manager.v2.kernel.response import (
    KernelClusterInfoGQLDTO,
    KernelLifecycleInfoGQLDTO,
    KernelNetworkInfoGQLDTO,
    KernelNode,
    KernelResourceInfoGQLDTO,
    KernelSessionInfoGQLDTO,
    KernelUserInfoGQLDTO,
    ResourceAllocationGQLDTO,
)
from ai.backend.common.dto.manager.v2.kernel.types import (
    KernelStatusFilter,
)
from ai.backend.common.types import AgentId, KernelId, SessionTypes
from ai.backend.manager.api.gql.base import OrderDirection, UUIDFilter
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

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.resource_slot.types import (
        KernelResourceAllocationFilterGQL,
        KernelResourceAllocationOrderByGQL,
        ResourceAllocationConnectionGQL,
    )
    from ai.backend.manager.api.gql.session.types import SessionV2GQL

from ai.backend.manager.api.gql.agent.types import AgentV2GQL
from ai.backend.manager.api.gql.common.types import (
    ResourceOptsGQL,
    ServicePortsGQL,
    SessionV2ResultGQL,
)
from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL
from ai.backend.manager.api.gql.fair_share.types.common import ResourceSlotGQL
from ai.backend.manager.api.gql.project_v2.types.node import ProjectV2GQL
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.resource_group.types import ResourceGroupGQL
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.user.types.node import UserV2GQL


@gql_enum(
    BackendAIGQLMeta(added_version="26.2.0", description="Status of a kernel in its lifecycle."),
    name="KernelV2Status",
)
class KernelV2StatusGQL(StrEnum):
    """GraphQL enum for kernel status."""

    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    PREPARING = "PREPARING"
    PREPARED = "PREPARED"
    CREATING = "CREATING"
    RUNNING = "RUNNING"
    TERMINATING = "TERMINATING"
    TERMINATED = "TERMINATED"
    CANCELLED = "CANCELLED"


@gql_enum(
    BackendAIGQLMeta(added_version="26.2.0", description="Fields available for ordering kernels."),
    name="KernelV2OrderField",
)
class KernelV2OrderFieldGQL(StrEnum):
    CREATED_AT = "created_at"
    TERMINATED_AT = "terminated_at"
    STATUS = "status"
    CLUSTER_MODE = "cluster_mode"
    CLUSTER_HOSTNAME = "cluster_hostname"
    CLUSTER_IDX = "cluster_idx"


@gql_pydantic_input(
    BackendAIGQLMeta(description="Filter for kernel status.", added_version="26.2.0"),
    name="KernelV2StatusFilter",
)
class KernelV2StatusFilterGQL(PydanticInputMixin[KernelStatusFilter]):
    in_: list[KernelV2StatusGQL] | None = gql_field(
        description="The in  field.", name="in", default=None
    )
    not_in: list[KernelV2StatusGQL] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter criteria for querying kernels.",
        added_version="26.2.0",
    ),
    name="KernelV2Filter",
)
class KernelV2FilterGQL(PydanticInputMixin[KernelFilter]):
    id: UUIDFilter | None = None
    status: KernelV2StatusFilterGQL | None = None
    session_id: UUIDFilter | None = None

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(description="Ordering specification for kernels.", added_version="26.2.0"),
    name="KernelV2OrderBy",
)
class KernelV2OrderByGQL(PydanticInputMixin[KernelOrder]):
    field: KernelV2OrderFieldGQL
    direction: OrderDirection = OrderDirection.DESC


# ========== Kernel Sub-Info Types ==========


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Information about the session this kernel belongs to.",
    ),
    model=KernelSessionInfoGQLDTO,
    name="KernelV2SessionInfo",
)
class KernelV2SessionInfoGQL:
    session_id: UUID = gql_field(
        description="The unique identifier of the session this kernel belongs to."
    )
    creation_id: str | None = gql_field(
        description="The creation ID used when creating the session."
    )
    name: str | None = gql_field(description="The name of the session.")
    session_type: SessionTypes = gql_field(
        description="The type of session (INTERACTIVE, BATCH, INFERENCE, SYSTEM)."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Cluster configuration for a kernel in distributed sessions.",
    ),
    model=KernelClusterInfoGQLDTO,
    name="KernelV2ClusterInfo",
)
class KernelV2ClusterInfoGQL:
    cluster_role: str = gql_field(
        description="The role of this kernel in the cluster (e.g., main, sub)."
    )
    cluster_idx: int = gql_field(
        description="The index of this kernel within the cluster (0-based)."
    )
    local_rank: int = gql_field(
        description="The local rank of this kernel for distributed computing."
    )
    cluster_hostname: str = gql_field(
        description="The hostname assigned to this kernel within the cluster network."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="User and ownership information for a kernel.",
    ),
    model=KernelUserInfoGQLDTO,
    name="KernelV2UserInfo",
)
class KernelV2UserInfoGQL:
    user_id: UUID | None = gql_field(description="The UUID of the user who owns this kernel.")
    access_key: str | None = gql_field(description="The access key used to create this kernel.")
    domain_name: str | None = gql_field(description="The domain this kernel belongs to.")
    group_id: UUID | None = gql_field(description="The group (project) ID this kernel belongs to.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Resource allocation with requested and used slots.",
    ),
    model=ResourceAllocationGQLDTO,
    name="ResourceAllocation",
)
class ResourceAllocationGQL:
    requested: ResourceSlotGQL = gql_field(
        description="The resource slots originally requested for this kernel."
    )
    used: ResourceSlotGQL | None = gql_field(
        description="The resource slots currently used by this kernel. May be null if not yet allocated."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Resource allocation information for a kernel.",
    ),
    model=KernelResourceInfoGQLDTO,
    name="KernelV2ResourceInfo",
)
class KernelV2ResourceInfoGQL:
    agent_id: str | None = gql_field(
        description="The ID of the agent running this kernel. Null if not yet assigned or hidden."
    )
    resource_group_name: str | None = gql_field(
        description="The resource group (scaling group) this kernel is assigned to."
    )
    container_id: str | None = gql_field(
        description="The container ID on the agent. Null if container not yet created or hidden."
    )
    allocation: ResourceAllocationGQL = gql_field(
        description="Resource allocation with requested and used slots."
    )
    shares: ResourceSlotGQL = gql_field(
        description="The fractional resource shares occupied by this kernel."
    )
    resource_opts: ResourceOptsGQL | None = gql_field(
        description="Additional resource options and configurations for this kernel."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Network configuration for a kernel.",
    ),
    model=KernelNetworkInfoGQLDTO,
    name="KernelV2NetworkInfo",
)
class KernelV2NetworkInfoGQL:
    service_ports: ServicePortsGQL | None = gql_field(
        description="Collection of service ports exposed by this kernel."
    )
    preopen_ports: list[int] | None = gql_field(
        description="List of ports that are pre-opened for this kernel."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Lifecycle and status information for a kernel.",
    ),
    model=KernelLifecycleInfoGQLDTO,
    name="KernelV2LifecycleInfo",
)
class KernelV2LifecycleInfoGQL:
    status: KernelV2StatusGQL = gql_field(
        description="Current status of the kernel (e.g., PENDING, RUNNING, TERMINATED). Indicates the kernel's position in its lifecycle."
    )
    result: SessionV2ResultGQL = gql_field(
        description="The result of the kernel execution (UNDEFINED, SUCCESS, FAILURE)."
    )
    created_at: datetime | None = gql_field(description="Timestamp when the kernel was created.")
    terminated_at: datetime | None = gql_field(
        description="Timestamp when the kernel was terminated. Null if still active."
    )
    starts_at: datetime | None = gql_field(
        description="Scheduled start time for the kernel, if applicable."
    )


# ========== Main Kernel Type ==========


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Represents a kernel (compute container) in Backend.AI.",
    ),
    name="KernelV2",
)
class KernelV2GQL(PydanticNodeMixin[KernelNode]):
    """Kernel type representing a compute container."""

    id: NodeID[str]

    # Inlined fields (from single-element types)
    startup_command: str | None = gql_field(
        description="Startup command executed when the kernel starts."
    )

    # Sub-info types
    session_info: KernelV2SessionInfoGQL = gql_field(
        description="Information about the session this kernel belongs to."
    )
    user_info: KernelV2UserInfoGQL = gql_field(description="User and ownership information.")
    network: KernelV2NetworkInfoGQL = gql_field(
        description="Network configuration and exposed ports."
    )
    cluster: KernelV2ClusterInfoGQL = gql_field(
        description="Cluster configuration for distributed computing."
    )
    resource: KernelV2ResourceInfoGQL = gql_field(
        description="Resource allocation and agent information."
    )
    lifecycle: KernelV2LifecycleInfoGQL = gql_field(description="Lifecycle status and timestamps.")

    @gql_added_field(
        BackendAIGQLMeta(added_version="26.2.0", description="The agent running this kernel.")
    )  # type: ignore[misc]
    async def agent(self, info: Info[StrawberryGQLContext]) -> AgentV2GQL | None:
        if self.resource.agent_id is None:
            return None
        agent_data = await info.context.data_loaders.agent_loader.load(
            AgentId(self.resource.agent_id)
        )
        if agent_data is None:
            return None
        return agent_data

    @gql_added_field(
        BackendAIGQLMeta(added_version="26.2.0", description="The user who owns this kernel.")
    )  # type: ignore[misc]
    async def user(self, info: Info[StrawberryGQLContext]) -> UserV2GQL | None:
        if self.user_info.user_id is None:
            return None
        user_data = await info.context.data_loaders.user_loader.load(self.user_info.user_id)
        if user_data is None:
            return None
        return user_data

    @gql_added_field(
        BackendAIGQLMeta(added_version="26.2.0", description="The project this kernel belongs to.")
    )  # type: ignore[misc]
    async def project(self, info: Info[StrawberryGQLContext]) -> ProjectV2GQL | None:
        if self.user_info.group_id is None:
            return None
        project_data = await info.context.data_loaders.project_loader.load(self.user_info.group_id)
        if project_data is None:
            return None
        return project_data

    @gql_added_field(
        BackendAIGQLMeta(added_version="26.2.0", description="The domain this kernel belongs to.")
    )  # type: ignore[misc]
    async def domain(self, info: Info[StrawberryGQLContext]) -> DomainV2GQL | None:
        if self.user_info.domain_name is None:
            return None
        return await info.context.data_loaders.domain_loader.load(self.user_info.domain_name)

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.2.0", description="The resource group this kernel is assigned to."
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
        BackendAIGQLMeta(added_version="26.3.0", description="The session this kernel belongs to.")
    )  # type: ignore[misc]
    async def session(
        self,
    ) -> (
        Annotated[
            SessionV2GQL,
            strawberry.lazy("ai.backend.manager.api.gql.session.types"),
        ]
        | None
    ):
        raise NotImplementedError

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.3.0", description="Per-slot resource allocation for this kernel."
        )
    )  # type: ignore[misc]
    async def resource_allocations(
        self,
        info: Info[StrawberryGQLContext],
        filter: Annotated[
            KernelResourceAllocationFilterGQL,
            strawberry.lazy("ai.backend.manager.api.gql.resource_slot.types"),
        ]
        | None = None,
        order_by: list[
            Annotated[
                KernelResourceAllocationOrderByGQL,
                strawberry.lazy("ai.backend.manager.api.gql.resource_slot.types"),
            ]
        ]
        | None = None,
        first: int | None = None,
        after: str | None = None,
        last: int | None = None,
        before: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Annotated[
        ResourceAllocationConnectionGQL,
        strawberry.lazy("ai.backend.manager.api.gql.resource_slot.types"),
    ]:
        """Fetch per-slot resource allocation for this kernel."""
        import uuid as _uuid
        from decimal import Decimal

        import strawberry as _strawberry

        from ai.backend.common.dto.manager.query import UUIDFilter as UUIDFilterDTO
        from ai.backend.common.dto.manager.v2.resource_slot.request import (
            AdminSearchResourceAllocationsInput,
        )
        from ai.backend.common.dto.manager.v2.resource_slot.request import (
            ResourceAllocationFilter as ResourceAllocationFilterDTO,
        )
        from ai.backend.common.dto.manager.v2.resource_slot.request import (
            ResourceAllocationOrder as ResourceAllocationOrderDTO,
        )
        from ai.backend.manager.api.gql.base import encode_cursor
        from ai.backend.manager.api.gql.resource_slot.types import (
            KernelResourceAllocationEdgeGQL,
            KernelResourceAllocationGQL,
            ResourceAllocationConnectionGQL,
        )

        kernel_id = str(self.id)
        pydantic_filter: ResourceAllocationFilterDTO | None = None
        if filter is not None:
            pydantic_filter = filter.to_pydantic()
            if pydantic_filter.kernel_id is None:
                pydantic_filter = ResourceAllocationFilterDTO(
                    slot_name=pydantic_filter.slot_name,
                    kernel_id=UUIDFilterDTO(equals=_uuid.UUID(kernel_id)),
                    AND=pydantic_filter.AND,
                    OR=pydantic_filter.OR,
                    NOT=pydantic_filter.NOT,
                )
        else:
            pydantic_filter = ResourceAllocationFilterDTO(
                kernel_id=UUIDFilterDTO(equals=_uuid.UUID(kernel_id)),
            )

        pydantic_order: list[ResourceAllocationOrderDTO] | None = (
            [o.to_pydantic() for o in order_by] if order_by is not None else None
        )

        search_input = AdminSearchResourceAllocationsInput(
            filter=pydantic_filter,
            order=pydantic_order,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
        payload = await info.context.adapters.resource_slot.search_allocations(search_input)

        edges = []
        for item in payload.items:
            slot_name = item.slot_name
            node = KernelResourceAllocationGQL(
                id=_strawberry.ID(item.id),
                slot_name=slot_name,
                requested=Decimal(item.requested),
                used=Decimal(item.used) if item.used is not None else None,
            )
            cursor = encode_cursor(slot_name)
            edges.append(KernelResourceAllocationEdgeGQL(node=node, cursor=cursor))

        return ResourceAllocationConnectionGQL(
            count=payload.total_count,
            edges=edges,
            page_info=_strawberry.relay.PageInfo(
                has_next_page=payload.has_next_page,
                has_previous_page=payload.has_previous_page,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
        )

    @classmethod
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.kernel_loader.load_many([
            KernelId(UUID(nid)) for nid in node_ids
        ])
        return cast(list[Self | None], results)


KernelV2EdgeGQL = Edge[KernelV2GQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Connection type for paginated kernel results.",
    ),
    name="KernelV2Connection",
)
class KernelV2ConnectionGQL(Connection[KernelV2GQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
