"""GraphQL types for kernel management."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Self
from uuid import UUID

import strawberry
from strawberry import ID
from strawberry.relay import Connection, Edge, Node, NodeID
from strawberry.scalars import JSON

from ai.backend.common.types import SessionId
from ai.backend.manager.api.gql.base import (
    OrderDirection,
)
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.data.kernel.types import KernelInfo, KernelStatus
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder
from ai.backend.manager.repositories.scheduler.options import KernelConditions, KernelOrders

KernelStatusGQL = strawberry.enum(KernelStatus, name="KernelStatus", description="Added in 26.1.0")


@strawberry.enum(
    name="KernelOrderField", description="Added in 26.1.0. Fields available for ordering kernels."
)
class KernelOrderFieldGQL(StrEnum):
    CREATED_AT = "created_at"
    ID = "id"


@strawberry.input(
    name="KernelStatusFilter", description="Added in 26.1.0. Filter for kernel status."
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
    name="KernelFilter", description="Added in 26.1.0. Filter criteria for querying kernels."
)
class KernelFilterGQL(GQLFilter):
    status: KernelStatusFilterGQL | None = None
    session_id: UUID | None = None

    def build_conditions(self) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if self.status:
            condition = self.status.build_condition()
            if condition:
                conditions.append(condition)
        if self.session_id:
            conditions.append(KernelConditions.by_session_ids([SessionId(self.session_id)]))
        return conditions


@strawberry.input(
    name="KernelOrderBy", description="Added in 26.1.0. Ordering specification for kernels."
)
class KernelOrderByGQL(GQLOrderBy):
    field: KernelOrderFieldGQL
    direction: OrderDirection = OrderDirection.DESC

    def to_query_order(self) -> QueryOrder:
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case KernelOrderFieldGQL.CREATED_AT:
                return KernelOrders.created_at(ascending)
            case KernelOrderFieldGQL.ID:
                return KernelOrders.id(ascending)


@strawberry.type(
    name="KernelSessionInfo",
    description="Added in 26.1.0. Information about the session this kernel belongs to.",
)
class KernelSessionInfoGQL:
    session_id: UUID = strawberry.field(
        description="The unique identifier of the session this kernel belongs to."
    )
    creation_id: str | None = strawberry.field(
        description="The creation ID used when creating the session."
    )
    name: str | None = strawberry.field(description="The name of the session.")
    session_type: str = strawberry.field(
        description="The type of session (e.g., INTERACTIVE, BATCH)."
    )


@strawberry.type(
    name="KernelClusterInfo",
    description="Added in 26.1.0. Cluster configuration for a kernel in distributed sessions.",
)
class KernelClusterInfoGQL:
    cluster_mode: str = strawberry.field(
        description="The clustering mode (e.g., single-node, multi-node)."
    )
    cluster_size: int = strawberry.field(description="Total number of nodes in the cluster.")
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
    name="KernelUserPermissionInfo",
    description="Added in 26.1.0. User permission and ownership information for a kernel.",
)
class KernelUserPermissionInfoGQL:
    user_uuid: UUID = strawberry.field(description="The UUID of the user who owns this kernel.")
    access_key: str = strawberry.field(description="The access key used to create this kernel.")
    domain_name: str = strawberry.field(description="The domain this kernel belongs to.")
    group_id: UUID = strawberry.field(description="The group (project) ID this kernel belongs to.")
    uid: int | None = strawberry.field(
        description="The Unix user ID for the kernel's container process."
    )
    main_gid: int | None = strawberry.field(
        description="The primary Unix group ID for the kernel's container process."
    )
    gids: list[int] | None = strawberry.field(
        description="Additional Unix group IDs for the kernel's container process."
    )


@strawberry.type(
    name="KernelImageInfo",
    description="Added in 26.1.0. Container image information for a kernel.",
)
class KernelImageInfoGQL:
    reference: str = strawberry.field(
        description="The canonical reference of the container image (e.g., registry/repo:tag)."
    )
    registry: str | None = strawberry.field(description="The container registry hosting the image.")
    tag: str | None = strawberry.field(description="The tag of the container image.")
    architecture: str = strawberry.field(
        description="The CPU architecture the image is built for (e.g., x86_64, aarch64)."
    )


@strawberry.type(
    name="KernelResourceInfo",
    description="Added in 26.1.0. Resource allocation information for a kernel.",
)
class KernelResourceInfoGQL:
    scaling_group: str | None = strawberry.field(
        description="The scaling group this kernel is assigned to."
    )
    agent_id: str | None = strawberry.field(
        description="The ID of the agent running this kernel. Null if not yet assigned or hidden."
    )
    agent_addr: str | None = strawberry.field(
        description="The network address of the agent. Null if not yet assigned or hidden."
    )
    container_id: str | None = strawberry.field(
        description="The container ID on the agent. Null if container not yet created or hidden."
    )
    occupied_slots: JSON = strawberry.field(
        description=dedent_strip("""
            The resource slots currently occupied by this kernel.
            Expressed as a JSON object with resource types as keys (e.g., cpu, mem, cuda.shares).
        """)
    )
    requested_slots: JSON = strawberry.field(
        description=dedent_strip("""
            The resource slots originally requested for this kernel.
            May differ from occupied_slots due to scheduling adjustments.
        """)
    )
    occupied_shares: JSON = strawberry.field(
        description="The fractional resource shares occupied by this kernel."
    )
    attached_devices: JSON = strawberry.field(
        description="Information about attached devices (e.g., GPUs) allocated to this kernel."
    )
    resource_opts: JSON | None = strawberry.field(
        description="Additional resource options and configurations for this kernel."
    )


@strawberry.type(
    name="KernelRuntimeInfo",
    description="Added in 26.1.0. Runtime configuration for a kernel.",
)
class KernelRuntimeInfoGQL:
    environ: list[str] | None = strawberry.field(
        description="Environment variables set for this kernel."
    )
    bootstrap_script: str | None = strawberry.field(
        description="Bootstrap script executed when the kernel starts."
    )
    startup_command: str | None = strawberry.field(
        description="Startup command executed after bootstrap."
    )


@strawberry.type(
    name="KernelNetworkInfo",
    description="Added in 26.1.0. Network configuration for a kernel.",
)
class KernelNetworkInfoGQL:
    kernel_host: str | None = strawberry.field(
        description="The hostname or IP address where the kernel is accessible."
    )
    repl_in_port: int = strawberry.field(description="The port for REPL input stream.")
    repl_out_port: int = strawberry.field(description="The port for REPL output stream.")
    service_ports: JSON | None = strawberry.field(
        description="Mapping of service names to their exposed ports."
    )
    preopen_ports: list[int] | None = strawberry.field(
        description="List of ports that are pre-opened for this kernel."
    )
    use_host_network: bool = strawberry.field(
        description="Whether the kernel uses host network mode."
    )


@strawberry.type(
    name="KernelLifecycleInfo",
    description="Added in 26.1.0. Lifecycle and status information for a kernel.",
)
class KernelLifecycleInfoGQL:
    status: KernelStatusGQL = strawberry.field(
        description=dedent_strip("""
            Current status of the kernel (e.g., PENDING, RUNNING, TERMINATED).
            Indicates the kernel's position in its lifecycle.
        """)
    )
    result: str = strawberry.field(
        description="The result of the kernel execution (e.g., SUCCESS, FAILURE)."
    )
    status_changed: datetime | None = strawberry.field(
        description="Timestamp when the kernel last changed status."
    )
    status_info: str | None = strawberry.field(
        description="Human-readable information about the current status."
    )
    status_data: JSON | None = strawberry.field(
        description="Additional structured data about the current status."
    )
    status_history: JSON | None = strawberry.field(
        description="History of status transitions with timestamps."
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
    last_seen: datetime | None = strawberry.field(
        description="Timestamp when the kernel was last seen active."
    )


@strawberry.type(
    name="KernelMetricsInfo",
    description="Added in 26.1.0. Metrics and statistics for a kernel.",
)
class KernelMetricsInfoGQL:
    num_queries: int = strawberry.field(
        description="The number of queries/executions performed by this kernel."
    )
    last_stat: JSON | None = strawberry.field(
        description="The last collected statistics for this kernel."
    )


@strawberry.type(
    name="KernelMetadataInfo",
    description="Added in 26.1.0. Additional metadata for a kernel.",
)
class KernelMetadataInfoGQL:
    callback_url: str | None = strawberry.field(
        description="URL to call back when kernel status changes."
    )
    internal_data: JSON | None = strawberry.field(
        description="Internal data stored with the kernel for system use."
    )


@strawberry.type(
    name="KernelV2",
    description="Added in 26.1.0. Represents a kernel (compute container) in Backend.AI.",
)
class KernelGQL(Node):
    """Kernel type representing a compute container."""

    id: NodeID[str]
    row_id: UUID = strawberry.field(description="The internal database row ID of the kernel.")

    session: KernelSessionInfoGQL = strawberry.field(
        description="Information about the session this kernel belongs to."
    )
    user_permission: KernelUserPermissionInfoGQL = strawberry.field(
        description="User permission and ownership information."
    )
    image: KernelImageInfoGQL = strawberry.field(description="Container image information.")
    network: KernelNetworkInfoGQL = strawberry.field(
        description="Network configuration and exposed ports."
    )
    cluster: KernelClusterInfoGQL = strawberry.field(
        description="Cluster configuration for distributed computing."
    )
    resource: KernelResourceInfoGQL = strawberry.field(
        description="Resource allocation and agent information."
    )
    runtime: KernelRuntimeInfoGQL = strawberry.field(
        description="Runtime configuration (environment, scripts)."
    )
    lifecycle: KernelLifecycleInfoGQL = strawberry.field(
        description="Lifecycle status and timestamps."
    )
    metrics: KernelMetricsInfoGQL = strawberry.field(
        description="Execution metrics and statistics."
    )
    metadata: KernelMetadataInfoGQL = strawberry.field(
        description="Additional metadata and internal data."
    )

    @classmethod
    def from_kernel_info(cls, kernel_info: KernelInfo, hide_agents: bool = False) -> Self:
        """Create KernelGQL from KernelInfo dataclass."""
        # Extract image reference from ImageInfo
        image_ref = ""
        architecture = ""
        registry = None
        tag = None
        if kernel_info.image.identifier:
            image_ref = kernel_info.image.identifier.canonical
            architecture = kernel_info.image.identifier.architecture
        if kernel_info.image.registry:
            registry = kernel_info.image.registry
        if kernel_info.image.tag:
            tag = kernel_info.image.tag
        if kernel_info.image.architecture:
            architecture = kernel_info.image.architecture

        return cls(
            id=ID(str(kernel_info.id)),
            row_id=kernel_info.id,
            session=KernelSessionInfoGQL(
                session_id=UUID(kernel_info.session.session_id),
                creation_id=kernel_info.session.creation_id,
                name=kernel_info.session.name,
                session_type=str(kernel_info.session.session_type),
            ),
            user_permission=KernelUserPermissionInfoGQL(
                user_uuid=kernel_info.user_permission.user_uuid,
                access_key=kernel_info.user_permission.access_key,
                domain_name=kernel_info.user_permission.domain_name,
                group_id=kernel_info.user_permission.group_id,
                uid=kernel_info.user_permission.uid,
                main_gid=kernel_info.user_permission.main_gid,
                gids=kernel_info.user_permission.gids,
            ),
            image=KernelImageInfoGQL(
                reference=image_ref,
                registry=registry,
                tag=tag,
                architecture=architecture,
            ),
            network=KernelNetworkInfoGQL(
                kernel_host=kernel_info.network.kernel_host,
                repl_in_port=kernel_info.network.repl_in_port,
                repl_out_port=kernel_info.network.repl_out_port,
                service_ports=kernel_info.network.service_ports,
                preopen_ports=kernel_info.network.preopen_ports,
                use_host_network=kernel_info.network.use_host_network,
            ),
            cluster=KernelClusterInfoGQL(
                cluster_mode=kernel_info.cluster.cluster_mode,
                cluster_size=kernel_info.cluster.cluster_size,
                cluster_role=kernel_info.cluster.cluster_role,
                cluster_idx=kernel_info.cluster.cluster_idx,
                local_rank=kernel_info.cluster.local_rank,
                cluster_hostname=kernel_info.cluster.cluster_hostname,
            ),
            resource=KernelResourceInfoGQL(
                scaling_group=kernel_info.resource.scaling_group,
                agent_id=kernel_info.resource.agent if not hide_agents else None,
                agent_addr=kernel_info.resource.agent_addr if not hide_agents else None,
                container_id=kernel_info.resource.container_id if not hide_agents else None,
                occupied_slots=kernel_info.resource.occupied_slots.to_json()
                if kernel_info.resource.occupied_slots
                else {},
                requested_slots=kernel_info.resource.requested_slots.to_json()
                if kernel_info.resource.requested_slots
                else {},
                occupied_shares=kernel_info.resource.occupied_shares or {},
                attached_devices=kernel_info.resource.attached_devices or {},
                resource_opts=kernel_info.resource.resource_opts,
            ),
            runtime=KernelRuntimeInfoGQL(
                environ=kernel_info.runtime.environ,
                bootstrap_script=kernel_info.runtime.bootstrap_script,
                startup_command=kernel_info.runtime.startup_command,
            ),
            lifecycle=KernelLifecycleInfoGQL(
                status=KernelStatusGQL(kernel_info.lifecycle.status),
                result=str(kernel_info.lifecycle.result),
                status_changed=kernel_info.lifecycle.status_changed,
                status_info=kernel_info.lifecycle.status_info,
                status_data=kernel_info.lifecycle.status_data,
                status_history=kernel_info.lifecycle.status_history,
                created_at=kernel_info.lifecycle.created_at,
                terminated_at=kernel_info.lifecycle.terminated_at,
                starts_at=kernel_info.lifecycle.starts_at,
                last_seen=kernel_info.lifecycle.last_seen,
            ),
            metrics=KernelMetricsInfoGQL(
                num_queries=kernel_info.metrics.num_queries,
                last_stat=kernel_info.metrics.last_stat,
            ),
            metadata=KernelMetadataInfoGQL(
                callback_url=kernel_info.metadata.callback_url,
                internal_data=kernel_info.metadata.internal_data,
            ),
        )


KernelEdgeGQL = Edge[KernelGQL]


@strawberry.type(
    name="KernelConnectionV2",
    description="Added in 26.1.0. Connection type for paginated kernel results.",
)
class KernelConnectionV2GQL(Connection[KernelGQL]):
    count: int

    def __init__(self, *args, count: int, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
