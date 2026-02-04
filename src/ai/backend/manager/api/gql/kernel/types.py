"""GraphQL types for kernel management."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Self
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.common.types import ImageID, SessionResult, SessionTypes
from ai.backend.manager.api.gql.base import OrderDirection, UUIDFilter
from ai.backend.manager.api.gql.image.types import ImageV2GQL

if TYPE_CHECKING:
    from ai.backend.manager.repositories.base import QueryCondition
from ai.backend.manager.api.gql.common.types import (
    ResourceOptsGQL,
    ServicePortEntryGQL,
    ServicePortsGQL,
)
from ai.backend.manager.api.gql.fair_share.types.common import ResourceSlotGQL
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.data.kernel.types import KernelInfo, KernelStatus
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder
from ai.backend.manager.repositories.scheduler.options import KernelConditions, KernelOrders


@strawberry.enum(
    name="KernelStatus",
    description="Added in 26.2.0. Status of a kernel in its lifecycle.",
)
class KernelStatusGQL(StrEnum):
    """GraphQL enum for kernel status."""

    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    PREPARING = "PREPARING"
    BUILDING = "BUILDING"
    PULLING = "PULLING"
    PREPARED = "PREPARED"
    CREATING = "CREATING"
    RUNNING = "RUNNING"
    RESTARTING = "RESTARTING"
    RESIZING = "RESIZING"
    SUSPENDED = "SUSPENDED"
    TERMINATING = "TERMINATING"
    TERMINATED = "TERMINATED"
    ERROR = "ERROR"
    CANCELLED = "CANCELLED"

    @classmethod
    def from_internal(cls, internal_status: KernelStatus) -> KernelStatusGQL:
        """Convert internal KernelStatus to GraphQL enum."""
        match internal_status:
            case KernelStatus.PENDING:
                return cls.PENDING
            case KernelStatus.SCHEDULED:
                return cls.SCHEDULED
            case KernelStatus.PREPARING:
                return cls.PREPARING
            case KernelStatus.BUILDING:
                return cls.BUILDING
            case KernelStatus.PULLING:
                return cls.PULLING
            case KernelStatus.PREPARED:
                return cls.PREPARED
            case KernelStatus.CREATING:
                return cls.CREATING
            case KernelStatus.RUNNING:
                return cls.RUNNING
            case KernelStatus.RESTARTING:
                return cls.RESTARTING
            case KernelStatus.RESIZING:
                return cls.RESIZING
            case KernelStatus.SUSPENDED:
                return cls.SUSPENDED
            case KernelStatus.TERMINATING:
                return cls.TERMINATING
            case KernelStatus.TERMINATED:
                return cls.TERMINATED
            case KernelStatus.ERROR:
                return cls.ERROR
            case KernelStatus.CANCELLED:
                return cls.CANCELLED

    def to_internal(self) -> KernelStatus:
        """Convert GraphQL enum to internal KernelStatus."""
        match self:
            case KernelStatusGQL.PENDING:
                return KernelStatus.PENDING
            case KernelStatusGQL.SCHEDULED:
                return KernelStatus.SCHEDULED
            case KernelStatusGQL.PREPARING:
                return KernelStatus.PREPARING
            case KernelStatusGQL.BUILDING:
                return KernelStatus.BUILDING
            case KernelStatusGQL.PULLING:
                return KernelStatus.PULLING
            case KernelStatusGQL.PREPARED:
                return KernelStatus.PREPARED
            case KernelStatusGQL.CREATING:
                return KernelStatus.CREATING
            case KernelStatusGQL.RUNNING:
                return KernelStatus.RUNNING
            case KernelStatusGQL.RESTARTING:
                return KernelStatus.RESTARTING
            case KernelStatusGQL.RESIZING:
                return KernelStatus.RESIZING
            case KernelStatusGQL.SUSPENDED:
                return KernelStatus.SUSPENDED
            case KernelStatusGQL.TERMINATING:
                return KernelStatus.TERMINATING
            case KernelStatusGQL.TERMINATED:
                return KernelStatus.TERMINATED
            case KernelStatusGQL.ERROR:
                return KernelStatus.ERROR
            case KernelStatusGQL.CANCELLED:
                return KernelStatus.CANCELLED


@dataclass(frozen=True)
class KernelStatusInMatchSpec:
    """Specification for KernelStatus IN operations (IN, NOT IN)."""

    values: list[KernelStatus]
    negated: bool


@strawberry.enum(
    name="KernelOrderField", description="Added in 26.2.0. Fields available for ordering kernels."
)
class KernelOrderFieldGQL(StrEnum):
    CREATED_AT = "created_at"
    TERMINATED_AT = "terminated_at"
    STATUS = "status"
    CLUSTER_MODE = "cluster_mode"
    CLUSTER_HOSTNAME = "cluster_hostname"
    CLUSTER_IDX = "cluster_idx"


@strawberry.input(
    name="KernelStatusFilter", description="Added in 26.2.0. Filter for kernel status."
)
class KernelStatusFilterGQL:
    in_: list[KernelStatusGQL] | None = strawberry.field(name="in", default=None)
    not_in: list[KernelStatusGQL] | None = None

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
    name="SessionScope",
    description="Added in 26.2.0. Scope for querying resources within a specific session.",
)
class SessionScopeGQL:
    """Scope for session-level queries."""

    session_id: UUID = strawberry.field(
        description="Session UUID to scope the query. Only resources belonging to this session will be returned."
    )


@strawberry.input(
    name="KernelFilter", description="Added in 26.2.0. Filter criteria for querying kernels."
)
class KernelFilterGQL(GQLFilter):
    id: UUIDFilter | None = None
    status: KernelStatusFilterGQL | None = None
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
    name="KernelOrderBy", description="Added in 26.2.0. Ordering specification for kernels."
)
class KernelOrderByGQL(GQLOrderBy):
    field: KernelOrderFieldGQL
    direction: OrderDirection = OrderDirection.DESC

    def to_query_order(self) -> QueryOrder:
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case KernelOrderFieldGQL.CREATED_AT:
                return KernelOrders.created_at(ascending)
            case KernelOrderFieldGQL.TERMINATED_AT:
                return KernelOrders.terminated_at(ascending)
            case KernelOrderFieldGQL.STATUS:
                return KernelOrders.status(ascending)
            case KernelOrderFieldGQL.CLUSTER_MODE:
                return KernelOrders.cluster_mode(ascending)
            case KernelOrderFieldGQL.CLUSTER_HOSTNAME:
                return KernelOrders.cluster_hostname(ascending)
            case KernelOrderFieldGQL.CLUSTER_IDX:
                return KernelOrders.cluster_idx(ascending)
            case _:
                raise ValueError(f"Unhandled KernelOrderFieldGQL value: {self.field!r}")


# ========== Kernel Sub-Info Types ==========


@strawberry.type(
    name="KernelSessionInfo",
    description="Added in 26.2.0. Information about the session this kernel belongs to.",
)
class KernelSessionInfoGQL:
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
    name="KernelClusterInfo",
    description="Added in 26.2.0. Cluster configuration for a kernel in distributed sessions.",
)
class KernelClusterInfoGQL:
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
    name="KernelUserInfo",
    description="Added in 26.2.0. User and ownership information for a kernel.",
)
class KernelUserInfoGQL:
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
    name="KernelResourceInfo",
    description="Added in 26.2.0. Resource allocation information for a kernel.",
)
class KernelResourceInfoGQL:
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
    name="KernelNetworkInfo",
    description="Added in 26.2.0. Network configuration for a kernel.",
)
class KernelNetworkInfoGQL:
    service_ports: ServicePortsGQL | None = strawberry.field(
        description="Collection of service ports exposed by this kernel."
    )
    preopen_ports: list[int] | None = strawberry.field(
        description="List of ports that are pre-opened for this kernel."
    )


@strawberry.type(
    name="KernelLifecycleInfo",
    description="Added in 26.2.0. Lifecycle and status information for a kernel.",
)
class KernelLifecycleInfoGQL:
    status: KernelStatusGQL = strawberry.field(
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
    image_id: UUID | None = strawberry.field(
        description="The UUID of the container image used by this kernel."
    )
    startup_command: str | None = strawberry.field(
        description="Startup command executed when the kernel starts."
    )

    # Sub-info types
    session: KernelSessionInfoGQL = strawberry.field(
        description="Information about the session this kernel belongs to."
    )
    user: KernelUserInfoGQL = strawberry.field(description="User and ownership information.")
    network: KernelNetworkInfoGQL = strawberry.field(
        description="Network configuration and exposed ports."
    )
    cluster: KernelClusterInfoGQL = strawberry.field(
        description="Cluster configuration for distributed computing."
    )
    resource: KernelResourceInfoGQL = strawberry.field(
        description="Resource allocation and agent information."
    )
    lifecycle: KernelLifecycleInfoGQL = strawberry.field(
        description="Lifecycle status and timestamps."
    )

    @strawberry.field(description="The container image used by this kernel.")  # type: ignore[misc]
    async def image(self, info: Info[StrawberryGQLContext]) -> ImageV2GQL | None:
        """Resolve the image for this kernel."""
        if self.image_id is None:
            return None
        image_data = await info.context.data_loaders.image_loader.load(ImageID(self.image_id))
        if image_data is None:
            return None
        return ImageV2GQL.from_data(image_data)

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
            image_id=kernel_info.image.image_id,
            startup_command=kernel_info.runtime.startup_command,
            session=KernelSessionInfoGQL(
                session_id=UUID(kernel_info.session.session_id),
                creation_id=kernel_info.session.creation_id,
                name=kernel_info.session.name,
                session_type=SessionTypes(kernel_info.session.session_type),
            ),
            user=KernelUserInfoGQL(
                user_id=kernel_info.user_permission.user_uuid,
                access_key=kernel_info.user_permission.access_key,
                domain_name=kernel_info.user_permission.domain_name,
                group_id=kernel_info.user_permission.group_id,
            ),
            network=KernelNetworkInfoGQL(
                service_ports=service_ports,
                preopen_ports=kernel_info.network.preopen_ports,
            ),
            cluster=KernelClusterInfoGQL(
                cluster_role=kernel_info.cluster.cluster_role,
                cluster_idx=kernel_info.cluster.cluster_idx,
                local_rank=kernel_info.cluster.local_rank,
                cluster_hostname=kernel_info.cluster.cluster_hostname,
            ),
            resource=KernelResourceInfoGQL(
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
            lifecycle=KernelLifecycleInfoGQL(
                status=KernelStatusGQL.from_internal(kernel_info.lifecycle.status),
                result=SessionResult(kernel_info.lifecycle.result),
                created_at=kernel_info.lifecycle.created_at,
                terminated_at=kernel_info.lifecycle.terminated_at,
                starts_at=kernel_info.lifecycle.starts_at,
            ),
        )


KernelEdgeGQL = Edge[KernelV2GQL]


@strawberry.type(
    name="KernelConnectionV2",
    description="Added in 26.2.0. Connection type for paginated kernel results.",
)
class KernelConnectionV2GQL(Connection[KernelV2GQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
