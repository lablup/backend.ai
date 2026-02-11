"""GraphQL types for kernel management."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Self
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.common.types import AgentId, KernelId, SessionResult, SessionTypes
from ai.backend.manager.api.gql.base import OrderDirection, UUIDFilter

if TYPE_CHECKING:
    from ai.backend.manager.repositories.base import QueryCondition

from ai.backend.manager.api.gql.agent.types import AgentV2GQL
from ai.backend.manager.api.gql.common.types import (
    ResourceOptsGQL,
    ServicePortEntryGQL,
    ServicePortsGQL,
)
from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL
from ai.backend.manager.api.gql.fair_share.types.common import ResourceSlotGQL
from ai.backend.manager.api.gql.project_v2.types.node import ProjectV2GQL
from ai.backend.manager.api.gql.resource_group.types import ResourceGroupGQL
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext
from ai.backend.manager.api.gql.user.types.node import UserV2GQL
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.data.kernel.types import KernelInfo, KernelStatus
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder
from ai.backend.manager.repositories.scheduler.options import KernelConditions, KernelOrders


@strawberry.enum(
    name="KernelV2Status",
    description="Added in 26.2.0. Status of a kernel in its lifecycle.",
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

    @classmethod
    def from_internal(cls, internal_status: KernelStatus) -> KernelV2StatusGQL:
        """Convert internal KernelStatus to GraphQL enum."""
        match internal_status:
            case KernelStatus.PENDING:
                return cls.PENDING
            case KernelStatus.SCHEDULED:
                return cls.SCHEDULED
            case KernelStatus.PREPARING | KernelStatus.PULLING:
                return cls.PREPARING
            case KernelStatus.PREPARED:
                return cls.PREPARED
            case KernelStatus.CREATING:
                return cls.CREATING
            case KernelStatus.RUNNING:
                return cls.RUNNING
            case KernelStatus.TERMINATING:
                return cls.TERMINATING
            case KernelStatus.TERMINATED:
                return cls.TERMINATED
            case (
                KernelStatus.CANCELLED
                | KernelStatus.BUILDING
                | KernelStatus.RESTARTING
                | KernelStatus.RESIZING
                | KernelStatus.SUSPENDED
                | KernelStatus.ERROR
            ):
                return cls.CANCELLED

    def to_internal(self) -> KernelStatus:
        """Convert GraphQL enum to internal KernelStatus."""
        match self:
            case KernelV2StatusGQL.PENDING:
                return KernelStatus.PENDING
            case KernelV2StatusGQL.SCHEDULED:
                return KernelStatus.SCHEDULED
            case KernelV2StatusGQL.PREPARING:
                return KernelStatus.PREPARING
            case KernelV2StatusGQL.PREPARED:
                return KernelStatus.PREPARED
            case KernelV2StatusGQL.CREATING:
                return KernelStatus.CREATING
            case KernelV2StatusGQL.RUNNING:
                return KernelStatus.RUNNING
            case KernelV2StatusGQL.TERMINATING:
                return KernelStatus.TERMINATING
            case KernelV2StatusGQL.TERMINATED:
                return KernelStatus.TERMINATED
            case KernelV2StatusGQL.CANCELLED:
                return KernelStatus.CANCELLED


@dataclass(frozen=True)
class KernelStatusInMatchSpec:
    """Specification for KernelStatus IN operations (IN, NOT IN)."""

    values: list[KernelStatus]
    negated: bool


@strawberry.enum(
    name="KernelV2OrderField", description="Added in 26.2.0. Fields available for ordering kernels."
)
class KernelV2OrderFieldGQL(StrEnum):
    CREATED_AT = "created_at"
    TERMINATED_AT = "terminated_at"
    STATUS = "status"
    CLUSTER_MODE = "cluster_mode"
    CLUSTER_HOSTNAME = "cluster_hostname"
    CLUSTER_IDX = "cluster_idx"


@strawberry.input(
    name="KernelV2StatusFilter", description="Added in 26.2.0. Filter for kernel status."
)
class KernelV2StatusFilterGQL:
    in_: list[KernelV2StatusGQL] | None = strawberry.field(name="in", default=None)
    not_in: list[KernelV2StatusGQL] | None = None

    def build_query_condition(
        self,
        in_factory: Callable[[KernelStatusInMatchSpec], QueryCondition],
    ) -> QueryCondition | None:
        """Build a query condition from this filter using the provided factory callable.

        Args:
            in_factory: Factory function for IN operations (IN, NOT IN)

        Returns:
            QueryCondition if any filter field is set, None otherwise
        """
        if self.in_:
            return in_factory(
                KernelStatusInMatchSpec(
                    values=[s.to_internal() for s in self.in_],
                    negated=False,
                )
            )
        if self.not_in:
            return in_factory(
                KernelStatusInMatchSpec(
                    values=[s.to_internal() for s in self.not_in],
                    negated=True,
                )
            )
        return None


@strawberry.input(
    name="KernelV2Filter", description="Added in 26.2.0. Filter criteria for querying kernels."
)
class KernelV2FilterGQL(GQLFilter):
    id: UUIDFilter | None = None
    status: KernelV2StatusFilterGQL | None = None
    session_id: UUIDFilter | None = None

    def build_conditions(self) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if self.id:
            condition = self.id.build_query_condition(
                KernelConditions.by_id_filter_equals,
                KernelConditions.by_id_filter_in,
            )
            if condition:
                conditions.append(condition)
        if self.status:
            condition = self.status.build_query_condition(
                KernelConditions.by_status_filter_in,
            )
            if condition:
                conditions.append(condition)
        if self.session_id:
            condition = self.session_id.build_query_condition(
                KernelConditions.by_session_id_filter_equals,
                KernelConditions.by_session_id_filter_in,
            )
            if condition:
                conditions.append(condition)
        return conditions


@strawberry.input(
    name="KernelV2OrderBy", description="Added in 26.2.0. Ordering specification for kernels."
)
class KernelV2OrderByGQL(GQLOrderBy):
    field: KernelV2OrderFieldGQL
    direction: OrderDirection = OrderDirection.DESC

    def to_query_order(self) -> QueryOrder:
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case KernelV2OrderFieldGQL.CREATED_AT:
                return KernelOrders.created_at(ascending)
            case KernelV2OrderFieldGQL.TERMINATED_AT:
                return KernelOrders.terminated_at(ascending)
            case KernelV2OrderFieldGQL.STATUS:
                return KernelOrders.status(ascending)
            case KernelV2OrderFieldGQL.CLUSTER_MODE:
                return KernelOrders.cluster_mode(ascending)
            case KernelV2OrderFieldGQL.CLUSTER_HOSTNAME:
                return KernelOrders.cluster_hostname(ascending)
            case KernelV2OrderFieldGQL.CLUSTER_IDX:
                return KernelOrders.cluster_idx(ascending)
            case _:
                raise ValueError(f"Unhandled KernelV2OrderFieldGQL value: {self.field!r}")


# ========== Kernel Sub-Info Types ==========


@strawberry.type(
    name="KernelV2SessionInfo",
    description="Added in 26.2.0. Information about the session this kernel belongs to.",
)
class KernelV2SessionInfoGQL:
    session_id: UUID = strawberry.field(
        description="The unique identifier of the session this kernel belongs to."
    )
    creation_id: str | None = strawberry.field(
        description="The creation ID used when creating the session."
    )
    name: str | None = strawberry.field(description="The name of the session.")
    session_type: SessionTypes = strawberry.field(
        description="The type of session (INTERACTIVE, BATCH, INFERENCE, SYSTEM)."
    )


@strawberry.type(
    name="KernelV2ClusterInfo",
    description="Added in 26.2.0. Cluster configuration for a kernel in distributed sessions.",
)
class KernelV2ClusterInfoGQL:
    cluster_role: str = strawberry.field(
        description="The role of this kernel in the cluster (e.g., main, sub)."
    )
    cluster_idx: int = strawberry.field(
        description="The index of this kernel within the cluster (0-based)."
    )
    local_rank: int = strawberry.field(
        description="The local rank of this kernel for distributed computing."
    )
    cluster_hostname: str = strawberry.field(
        description="The hostname assigned to this kernel within the cluster network."
    )


@strawberry.type(
    name="KernelV2UserInfo",
    description="Added in 26.2.0. User and ownership information for a kernel.",
)
class KernelV2UserInfoGQL:
    user_id: UUID | None = strawberry.field(
        description="The UUID of the user who owns this kernel."
    )
    access_key: str | None = strawberry.field(
        description="The access key used to create this kernel."
    )
    domain_name: str | None = strawberry.field(description="The domain this kernel belongs to.")
    group_id: UUID | None = strawberry.field(
        description="The group (project) ID this kernel belongs to."
    )


@strawberry.type(
    name="ResourceAllocation",
    description="Added in 26.2.0. Resource allocation with requested and used slots.",
)
class ResourceAllocationGQL:
    requested: ResourceSlotGQL = strawberry.field(
        description="The resource slots originally requested for this kernel."
    )
    used: ResourceSlotGQL | None = strawberry.field(
        description="The resource slots currently used by this kernel. May be null if not yet allocated."
    )


@strawberry.type(
    name="KernelV2ResourceInfo",
    description="Added in 26.2.0. Resource allocation information for a kernel.",
)
class KernelV2ResourceInfoGQL:
    agent_id: str | None = strawberry.field(
        description="The ID of the agent running this kernel. Null if not yet assigned or hidden."
    )
    resource_group_name: str | None = strawberry.field(
        description="The resource group (scaling group) this kernel is assigned to."
    )
    container_id: str | None = strawberry.field(
        description="The container ID on the agent. Null if container not yet created or hidden."
    )
    allocation: ResourceAllocationGQL = strawberry.field(
        description="Resource allocation with requested and used slots."
    )
    shares: ResourceSlotGQL = strawberry.field(
        description="The fractional resource shares occupied by this kernel."
    )
    resource_opts: ResourceOptsGQL | None = strawberry.field(
        description="Additional resource options and configurations for this kernel."
    )


@strawberry.type(
    name="KernelV2NetworkInfo",
    description="Added in 26.2.0. Network configuration for a kernel.",
)
class KernelV2NetworkInfoGQL:
    service_ports: ServicePortsGQL | None = strawberry.field(
        description="Collection of service ports exposed by this kernel."
    )
    preopen_ports: list[int] | None = strawberry.field(
        description="List of ports that are pre-opened for this kernel."
    )


@strawberry.type(
    name="KernelV2LifecycleInfo",
    description="Added in 26.2.0. Lifecycle and status information for a kernel.",
)
class KernelV2LifecycleInfoGQL:
    status: KernelV2StatusGQL = strawberry.field(
        description=dedent_strip("""
            Current status of the kernel (e.g., PENDING, RUNNING, TERMINATED).
            Indicates the kernel's position in its lifecycle.
        """)
    )
    result: SessionResult = strawberry.field(
        description="The result of the kernel execution (UNDEFINED, SUCCESS, FAILURE)."
    )
    created_at: datetime | None = strawberry.field(
        description="Timestamp when the kernel was created."
    )
    terminated_at: datetime | None = strawberry.field(
        description="Timestamp when the kernel was terminated. Null if still active."
    )
    starts_at: datetime | None = strawberry.field(
        description="Scheduled start time for the kernel, if applicable."
    )


# ========== Main Kernel Type ==========


@strawberry.type(
    name="KernelV2",
    description="Added in 26.2.0. Represents a kernel (compute container) in Backend.AI.",
)
class KernelV2GQL(Node):
    """Kernel type representing a compute container."""

    id: NodeID[str]

    # Inlined fields (from single-element types)
    startup_command: str | None = strawberry.field(
        description="Startup command executed when the kernel starts."
    )

    # Sub-info types
    session: KernelV2SessionInfoGQL = strawberry.field(
        description="Information about the session this kernel belongs to."
    )
    user_info: KernelV2UserInfoGQL = strawberry.field(description="User and ownership information.")
    network: KernelV2NetworkInfoGQL = strawberry.field(
        description="Network configuration and exposed ports."
    )
    cluster: KernelV2ClusterInfoGQL = strawberry.field(
        description="Cluster configuration for distributed computing."
    )
    resource: KernelV2ResourceInfoGQL = strawberry.field(
        description="Resource allocation and agent information."
    )
    lifecycle: KernelV2LifecycleInfoGQL = strawberry.field(
        description="Lifecycle status and timestamps."
    )

    @strawberry.field(  # type: ignore[misc]
        description="Added in 26.2.0. The agent running this kernel."
    )
    async def agent(self, info: Info[StrawberryGQLContext]) -> AgentV2GQL | None:
        if self.resource.agent_id is None:
            return None
        agent_data = await info.context.data_loaders.agent_loader.load(
            AgentId(self.resource.agent_id)
        )
        if agent_data is None:
            return None
        return AgentV2GQL.from_agent_detail_data(agent_data)

    @strawberry.field(  # type: ignore[misc]
        description="Added in 26.2.0. The user who owns this kernel."
    )
    async def user(self, info: Info[StrawberryGQLContext]) -> UserV2GQL | None:
        if self.user_info.user_id is None:
            return None
        user_data = await info.context.data_loaders.user_loader.load(self.user_info.user_id)
        if user_data is None:
            return None
        return UserV2GQL.from_data(user_data)

    @strawberry.field(  # type: ignore[misc]
        description="Added in 26.2.0. The project this kernel belongs to."
    )
    async def project(self, info: Info[StrawberryGQLContext]) -> ProjectV2GQL | None:
        if self.user_info.group_id is None:
            return None
        project_data = await info.context.data_loaders.project_loader.load(self.user_info.group_id)
        if project_data is None:
            return None
        return ProjectV2GQL.from_data(project_data)

    @strawberry.field(  # type: ignore[misc]
        description="Added in 26.2.0. The domain this kernel belongs to."
    )
    async def domain(self, info: Info[StrawberryGQLContext]) -> DomainV2GQL | None:
        if self.user_info.domain_name is None:
            return None
        domain_data = await info.context.data_loaders.domain_loader.load(self.user_info.domain_name)
        if domain_data is None:
            return None
        return DomainV2GQL.from_data(domain_data)

    @strawberry.field(  # type: ignore[misc]
        description="Added in 26.2.0. The resource group this kernel is assigned to."
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
        return [cls.from_kernel_info(data) if data is not None else None for data in results]

    @classmethod
    def from_kernel_info(cls, kernel_info: KernelInfo, hide_agents: bool = False) -> Self:
        """Create KernelGQL from KernelInfo dataclass."""
        service_ports = (
            ServicePortsGQL(
                entries=[
                    ServicePortEntryGQL.from_dict(p) for p in kernel_info.network.service_ports
                ]
            )
            if kernel_info.network.service_ports
            else None
        )

        used_slots = (
            ResourceSlotGQL.from_resource_slot(kernel_info.resource.occupied_slots)
            if kernel_info.resource.occupied_slots
            else None
        )

        requested_slots = (
            ResourceSlotGQL.from_resource_slot(kernel_info.resource.requested_slots)
            if kernel_info.resource.requested_slots
            else ResourceSlotGQL(entries=[])
        )

        shares = ResourceSlotGQL.from_resource_slot(kernel_info.resource.occupied_shares or {})

        return cls(
            id=ID(str(kernel_info.id)),
            startup_command=kernel_info.runtime.startup_command,
            session=KernelV2SessionInfoGQL(
                session_id=UUID(kernel_info.session.session_id),
                creation_id=kernel_info.session.creation_id,
                name=kernel_info.session.name,
                session_type=SessionTypes(kernel_info.session.session_type),
            ),
            user_info=KernelV2UserInfoGQL(
                user_id=kernel_info.user_permission.user_uuid,
                access_key=kernel_info.user_permission.access_key,
                domain_name=kernel_info.user_permission.domain_name,
                group_id=kernel_info.user_permission.group_id,
            ),
            network=KernelV2NetworkInfoGQL(
                service_ports=service_ports,
                preopen_ports=kernel_info.network.preopen_ports,
            ),
            cluster=KernelV2ClusterInfoGQL(
                cluster_role=kernel_info.cluster.cluster_role,
                cluster_idx=kernel_info.cluster.cluster_idx,
                local_rank=kernel_info.cluster.local_rank,
                cluster_hostname=kernel_info.cluster.cluster_hostname,
            ),
            resource=KernelV2ResourceInfoGQL(
                agent_id=kernel_info.resource.agent if not hide_agents else None,
                resource_group_name=kernel_info.resource.scaling_group,
                container_id=kernel_info.resource.container_id if not hide_agents else None,
                allocation=ResourceAllocationGQL(
                    requested=requested_slots,
                    used=used_slots,
                ),
                shares=shares,
                resource_opts=ResourceOptsGQL.from_mapping(kernel_info.resource.resource_opts),
            ),
            lifecycle=KernelV2LifecycleInfoGQL(
                status=KernelV2StatusGQL.from_internal(kernel_info.lifecycle.status),
                result=SessionResult(kernel_info.lifecycle.result),
                created_at=kernel_info.lifecycle.created_at,
                terminated_at=kernel_info.lifecycle.terminated_at,
                starts_at=kernel_info.lifecycle.starts_at,
            ),
        )


KernelV2EdgeGQL = Edge[KernelV2GQL]


@strawberry.type(
    name="KernelV2Connection",
    description="Added in 26.2.0. Connection type for paginated kernel results.",
)
class KernelV2ConnectionGQL(Connection[KernelV2GQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
