"""GraphQL types for kernel management."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Self
from uuid import UUID

import strawberry
from strawberry import ID
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.common.types import SessionResult, SessionTypes
from ai.backend.manager.api.gql.base import OrderDirection, UUIDFilter
from ai.backend.manager.api.gql.common.types import (
    ResourceOptsGQL,
    ServicePortEntryGQL,
    ServicePortsGQL,
)
from ai.backend.manager.api.gql.fair_share.types.common import ResourceSlotGQL
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.data.kernel.types import KernelInfo, KernelStatus
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder
from ai.backend.manager.repositories.scheduler.options import KernelConditions, KernelOrders

KernelStatusGQL = strawberry.enum(KernelStatus, name="KernelStatus", description="Added in 26.2.0")


@strawberry.enum(
    name="KernelOrderField", description="Added in 26.2.0. Fields available for ordering kernels."
)
class KernelOrderFieldGQL(StrEnum):
    CREATED_AT = "created_at"


@strawberry.input(
    name="KernelStatusFilter", description="Added in 26.2.0. Filter for kernel status."
)
class KernelStatusFilterGQL:
    in_: list[KernelStatusGQL] | None = strawberry.field(name="in", default=None)
    not_in: list[KernelStatusGQL] | None = None

    def build_condition(self) -> QueryCondition | None:
        if self.in_:
            return KernelConditions.by_statuses(self.in_)
        if self.not_in:
            # For not_in, we need all statuses except the ones in the list
            all_statuses = set(KernelStatus)
            allowed_statuses = all_statuses - set(self.not_in)
            return KernelConditions.by_statuses(list(allowed_statuses))
        return None


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
            condition = self.status.build_condition()
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
                status=KernelStatusGQL(kernel_info.lifecycle.status),
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

    def __init__(self, *args, count: int, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
