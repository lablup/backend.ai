"""GraphQL types for agent and kernel management."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Self
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID
from strawberry.scalars import JSON

from ai.backend.common.types import AgentId, SessionId
from ai.backend.manager.api.gql.base import (
    JSONString,
    OrderDirection,
    StringFilter,
)
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.data.agent.types import AgentDetailData, AgentStatus
from ai.backend.manager.data.kernel.types import KernelInfo, KernelStatus
from ai.backend.manager.models.rbac.permission_defs import AgentPermission
from ai.backend.manager.repositories.agent.options import AgentConditions, AgentOrders
from ai.backend.manager.repositories.base import (
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.scheduler.options import KernelConditions, KernelOrders

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.types import StrawberryGQLContext


# =============================================================================
# Agent-related types (existing from main branch)
# =============================================================================


@strawberry.enum(
    name="AgentPermission",
    description="Added in 26.1.0. Permissions related to agent operations",
)
class AgentPermissionGQL(StrEnum):
    READ_ATTRIBUTE = "read_attribute"
    UPDATE_ATTRIBUTE = "update_attribute"
    CREATE_COMPUTE_SESSION = "create_compute_session"
    CREATE_SERVICE = "create_service"

    @classmethod
    def from_agent_permission(cls, permission: AgentPermission) -> AgentPermissionGQL:
        match permission:
            case AgentPermission.READ_ATTRIBUTE:
                return AgentPermissionGQL.READ_ATTRIBUTE
            case AgentPermission.UPDATE_ATTRIBUTE:
                return AgentPermissionGQL.UPDATE_ATTRIBUTE
            case AgentPermission.CREATE_COMPUTE_SESSION:
                return AgentPermissionGQL.CREATE_COMPUTE_SESSION
            case AgentPermission.CREATE_SERVICE:
                return AgentPermissionGQL.CREATE_SERVICE


@strawberry.enum(
    name="AgentOrderField",
    description="Added in 26.1.0. Order by specification for agents",
)
class AgentOrderFieldGQL(StrEnum):
    ID = "id"
    FIRST_CONTACT = "first_contact"
    SCALING_GROUP = "scaling_group"
    SCHEDULABLE = "schedulable"


@strawberry.input(
    name="AgentStatusFilter",
    description=dedent_strip("""
        Added in 26.1.0. Filter options for agent status within AgentFilter.
        It includes options to filter whether agent status is in a specific list or equals a specific value.
    """),
)
class AgentStatusFilterGQL:
    in_: list[AgentStatus] | None = strawberry.field(name="in", default=None)
    equals: AgentStatus | None = None


@strawberry.input(
    name="AgentFilter", description="Added in 26.1.0. Filter options for querying agents"
)
class AgentFilterGQL(GQLFilter):
    id: StringFilter | None = None
    status: AgentStatusFilterGQL | None = None
    schedulable: bool | None = None
    scaling_group: StringFilter | None = None

    AND: list[AgentFilterGQL] | None = None
    OR: list[AgentFilterGQL] | None = None
    NOT: list[AgentFilterGQL] | None = None

    def build_conditions(self) -> list[QueryCondition]:
        field_conditions: list[QueryCondition] = []
        if self.id is not None:
            name_condition = self.id.build_query_condition(
                contains_factory=AgentConditions.by_id_contains,
                equals_factory=AgentConditions.by_id_equals,
                starts_with_factory=AgentConditions.by_id_starts_with,
                ends_with_factory=AgentConditions.by_id_ends_with,
            )
            if name_condition is not None:
                field_conditions.append(name_condition)
        if self.status is not None:
            if self.status.in_ is not None:
                field_conditions.append(AgentConditions.by_status_contains(self.status.in_))
            if self.status.equals is not None:
                field_conditions.append(AgentConditions.by_status_equals(self.status.equals))
        if self.schedulable is not None:
            field_conditions.append(AgentConditions.by_schedulable(self.schedulable))
        if self.scaling_group is not None:
            scaling_group_condition = self.scaling_group.build_query_condition(
                contains_factory=AgentConditions.by_scaling_group_contains,
                equals_factory=AgentConditions.by_scaling_group_equals,
                starts_with_factory=AgentConditions.by_scaling_group_starts_with,
                ends_with_factory=AgentConditions.by_scaling_group_ends_with,
            )
            if scaling_group_condition is not None:
                field_conditions.append(scaling_group_condition)

        if self.AND:
            for sub_filter in self.AND:
                field_conditions.extend(sub_filter.build_conditions())

        # Handle OR logical operator
        if self.OR:
            or_sub_conditions: list[QueryCondition] = []
            for sub_filter in self.OR:
                or_sub_conditions.extend(sub_filter.build_conditions())
            if or_sub_conditions:
                field_conditions.append(combine_conditions_or(or_sub_conditions))

        # Handle NOT logical operator
        if self.NOT:
            not_sub_conditions: list[QueryCondition] = []
            for sub_filter in self.NOT:
                not_sub_conditions.extend(sub_filter.build_conditions())
            if not_sub_conditions:
                field_conditions.append(negate_conditions(not_sub_conditions))

        return field_conditions


@strawberry.input(name="AgentOrderBy", description="Added in 26.1.0. Options for ordering agents")
class AgentOrderByGQL(GQLOrderBy):
    field: AgentOrderFieldGQL
    direction: OrderDirection = OrderDirection.ASC

    def to_query_order(self) -> QueryOrder:
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case AgentOrderFieldGQL.ID:
                return AgentOrders.id(ascending)
            case AgentOrderFieldGQL.FIRST_CONTACT:
                return AgentOrders.first_contact(ascending)
            case AgentOrderFieldGQL.SCALING_GROUP:
                return AgentOrders.scaling_group(ascending)
            case AgentOrderFieldGQL.SCHEDULABLE:
                return AgentOrders.schedulable(ascending)


@strawberry.type(name="AgentResource", description="Added in 25.15.0")
class AgentResourceGQL:
    capacity: JSON = strawberry.field(
        description=dedent_strip("""
            Total hardware resource capacity available on the agent.
            Expressed as a JSON object containing resource slots (e.g., cpu, mem, accelerators).
            Each slot represents the maximum amount of that resource type the agent can provide.
        """)
    )
    used: JSON = strawberry.field(
        description=dedent_strip("""
            Total amount of resources currently consumed by running and scheduled compute sessions.
            Includes both the requested resources for sessions being prepared and already allocated
            resources for active sessions. The sum of occupied resources across all session states
            that occupy agent resources (PREPARING, PULLING, RUNNING, RESTARTING, etc.).
            Expressed as a JSON object with the same structure as capacity.
        """)
    )
    free: JSON = strawberry.field(
        description=dedent_strip("""
            Available resources for scheduling new compute sessions (capacity - used).
            This represents the maximum resources that can be allocated to new sessions
            without exceeding the agent's capacity. Expressed as a JSON object with
            the same structure as capacity.
        """)
    )


@strawberry.type(name="AgentStats", description="Added in 25.15.0")
class AgentStatsGQL:
    total_resource: AgentResourceGQL = strawberry.field(description="Added in 25.15.0")


@strawberry.type(
    name="AgentStatusInfo",
    description="Added in 26.1.0. Status and lifecycle information for an agent",
)
class AgentStatusInfoGQL:
    status: AgentStatus = strawberry.field(
        description=dedent_strip("""
            Current operational status of the agent.
            Indicates whether the agent is ALIVE (active and reachable), LOST (unreachable),
            TERMINATED (intentionally stopped), or RESTARTING (in recovery process).
        """)
    )
    status_changed: datetime | None = strawberry.field(
        description=dedent_strip("""
            Timestamp when the agent last changed its status.
            Updated whenever the agent transitions between different status states
            (e.g., from ALIVE to LOST, or RESTARTING to ALIVE).
            Will be null if the agent status has never changed since initial registration.
        """)
    )
    first_contact: datetime | None = strawberry.field(
        description=dedent_strip("""
            Timestamp when the agent first registered with the manager.
            This value remains constant throughout the agent's lifecycle and can be used
            to track the agent's age or identify when it was initially deployed.
        """)
    )
    lost_at: datetime | None = strawberry.field(
        description=dedent_strip("""
            Timestamp when the agent was marked as lost or unreachable.
            Set when the manager detects the agent has stopped sending heartbeats.
            Will be null if the agent has never been lost or is currently alive.
        """)
    )
    schedulable: bool = strawberry.field(
        description=dedent_strip("""
            Indicates whether the agent is available for scheduling new compute sessions.
            An agent can be non-schedulable due to maintenance mode, resource constraints or other operational reasons by admin.
            When false, no new sessions will be assigned to this agent.
        """)
    )


@strawberry.type(
    name="AgentSystemInfo",
    description="Added in 26.1.0. System and configuration information for an agent",
)
class AgentSystemInfoGQL:
    architecture: str = strawberry.field(
        description=dedent_strip("""
            Hardware architecture of the agent's host system (e.g., "x86_64", "aarch64").
            Used to match compute sessions with compatible container images and ensure
            proper binary execution on the agent.
        """)
    )
    version: str = strawberry.field(
        description=dedent_strip("""
            Version string of the Backend.AI agent software running on this node.
            Follows semantic versioning (e.g., "26.1.0") and helps identify
            compatibility and available features.
        """)
    )
    auto_terminate_abusing_kernel: bool = strawberry.field(
        description=dedent_strip("""
            Legacy configuration flag, no longer actively used in the system.
            Retained for backward compatibility and schema consistency.
            Originally intended to control automatic termination of misbehaving sessions.
        """),
        deprecation_reason="Legacy feature no longer in use.",
    )
    compute_plugins: JSON = strawberry.field(
        description=dedent_strip("""
            List of compute plugin metadata supported by this agent.
            Each plugin represents a specific accelerator or resource type (e.g., CUDA).
            Expressed as a JSON object where keys are plugin names and values contain
            plugin-specific configuration and capabilities.
        """)
    )


@strawberry.type(
    name="AgentNetworkInfo",
    description="Added in 26.1.0. Network-related information for an agent",
)
class AgentNetworkInfoGQL:
    region: str = strawberry.field(description="Logical region where the agent is deployed.")
    addr: str = strawberry.field(
        description=dedent_strip("""
            Network address and port where the agent can be reached (format: "host:port").
            This is the bind or advertised address used by the manager to communicate
            with the agent for session lifecycle management and health monitoring.
        """)
    )


@strawberry.type(
    name="AgentV2", description="Added in 26.1.0. Strawberry-based Agent type replacing AgentNode."
)
class AgentV2GQL(Node):
    id: NodeID[str]
    _agent_id: strawberry.Private[AgentId]
    resource_info: AgentResourceGQL = strawberry.field(
        description=dedent_strip("""
            Hardware resource capacity, usage, and availability information.
            Contains capacity (total), used (occupied by sessions), and free (available) resource slots
            including CPU cores, memory, accelerators (GPUs, TPUs), and other compute resources.
        """)
    )
    status_info: AgentStatusInfoGQL = strawberry.field(
        description=dedent_strip("""
            Current operational status and lifecycle timestamps.
            Includes the agent's status (ALIVE, LOST, etc.), status change history,
            initial registration time, and schedulability state.
        """)
    )
    system_info: AgentSystemInfoGQL = strawberry.field(
        description=dedent_strip("""
            System configuration and software version information.
            Contains the host architecture, agent software version, and available compute plugins
            for accelerators and specialized hardware.
        """)
    )
    network_info: AgentNetworkInfoGQL = strawberry.field(
        description=dedent_strip("""
            Network location and connectivity information.
            Provides the agent's region and network address for manager-to-agent communication.
        """)
    )
    permissions: list[AgentPermissionGQL] = strawberry.field(
        description=dedent_strip("""
            List of permissions the current authenticated user has on this agent.
            Determines which operations (read attributes, create sessions, etc.)
            the user can perform on this specific agent based on RBAC policies.
        """)
    )
    scaling_group: str = strawberry.field(
        description=dedent_strip("""
            Name of the scaling group this agent belongs to.
            Scaling groups are logical collections of agents used for resource scheduling,
            quota management, and workload isolation across different user groups or projects.
        """)
    )

    @strawberry.field(
        description="Added in 26.1.0. List of kernels running on this agent with pagination support."
    )
    async def kernels(
        self,
        info: Info[StrawberryGQLContext],
        filter: KernelFilter | None = None,
        order_by: list[KernelOrderBy] | None = None,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
        resource_occupied_only: bool = False,
    ) -> KernelConnectionV2:
        """Fetch kernels associated with this agent."""
        from .fetcher import fetch_kernels_by_agent

        return await fetch_kernels_by_agent(
            info=info,
            agent_id=self._agent_id,
            filter=filter,
            order_by=order_by,
            before=before,
            after=after,
            first=first,
            last=last,
            limit=limit,
            offset=offset,
            resource_occupied_only=resource_occupied_only,
        )

    @classmethod
    def from_agent_detail_data(cls, detail_data: AgentDetailData) -> Self:
        data = detail_data.agent

        return cls(
            id=ID(data.id),
            _agent_id=AgentId(data.id),
            resource_info=AgentResourceGQL(
                capacity=data.available_slots.to_json(),
                used=data.actual_occupied_slots.to_json(),
                free=(data.available_slots - data.actual_occupied_slots).to_json(),
            ),
            status_info=AgentStatusInfoGQL(
                status=data.status,
                status_changed=data.status_changed,
                first_contact=data.first_contact,
                lost_at=data.lost_at,
                schedulable=data.schedulable,
            ),
            system_info=AgentSystemInfoGQL(
                architecture=data.architecture,
                version=data.version,
                auto_terminate_abusing_kernel=data.auto_terminate_abusing_kernel,
                compute_plugins=data.compute_plugins,
            ),
            network_info=AgentNetworkInfoGQL(
                region=data.region,
                addr=data.addr,
            ),
            permissions=[
                AgentPermissionGQL.from_agent_permission(p) for p in detail_data.permissions
            ],
            scaling_group=data.scaling_group,
        )


AgentV2Edge = Edge[AgentV2GQL]


@strawberry.type(
    description="Added in 26.1.0. Relay-style connection type for paginated lists of agents"
)
class AgentV2Connection(Connection[AgentV2GQL]):
    count: int

    def __init__(self, *args, count: int, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# =============================================================================
# Kernel-related types (new feature from kernel node resolver)
# =============================================================================


KernelStatusGQL = strawberry.enum(KernelStatus, name="KernelStatus", description="Added in 26.1.0")


@strawberry.enum(description="Added in 26.1.0. Fields available for ordering kernels.")
class KernelOrderField(StrEnum):
    CREATED_AT = "created_at"
    ID = "id"


@strawberry.input(description="Added in 26.1.0. Filter for kernel status.")
class KernelStatusFilter:
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


@strawberry.input(description="Added in 26.1.0. Filter criteria for querying kernels.")
class KernelFilter(GQLFilter):
    status: KernelStatusFilter | None = None
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


@strawberry.input(description="Added in 26.1.0. Ordering specification for kernels.")
class KernelOrderBy(GQLOrderBy):
    field: KernelOrderField
    direction: OrderDirection = OrderDirection.DESC

    def to_query_order(self) -> QueryOrder:
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case KernelOrderField.CREATED_AT:
                return KernelOrders.created_at(ascending)
            case KernelOrderField.ID:
                return KernelOrders.id(ascending)


@strawberry.type(
    name="KernelV2",
    description="Added in 26.1.0. Represents a kernel (compute container) in Backend.AI.",
)
class KernelGQL(Node):
    """
    Kernel type representing a compute container.
    """

    id: NodeID[str]
    row_id: UUID
    cluster_idx: int
    local_rank: int
    cluster_role: str
    cluster_hostname: str
    session_id: UUID

    # Image info
    image_reference: str
    architecture: str

    # Status
    status: KernelStatusGQL
    status_changed: datetime | None
    status_info: str | None
    status_data: JSON | None
    created_at: datetime | None
    terminated_at: datetime | None
    starts_at: datetime | None
    scheduled_at: datetime | None

    # Resources
    agent_id: str | None
    agent_addr: str | None
    container_id: str | None
    resource_opts: JSON | None
    occupied_slots: JSONString
    preopen_ports: list[int] | None

    @classmethod
    def from_kernel_info(cls, kernel_info: KernelInfo, hide_agents: bool = False) -> Self:
        """Create KernelGQL from KernelInfo dataclass."""
        status_history = kernel_info.lifecycle.status_history or {}

        # Extract image reference from ImageInfo
        image_ref = ""
        architecture = ""
        if kernel_info.image.identifier:
            image_ref = kernel_info.image.identifier.canonical
            architecture = kernel_info.image.identifier.architecture
        elif kernel_info.image.architecture:
            architecture = kernel_info.image.architecture

        return cls(
            id=ID(str(kernel_info.id)),
            row_id=kernel_info.id,
            cluster_idx=kernel_info.cluster.cluster_idx,
            local_rank=kernel_info.cluster.local_rank,
            cluster_role=kernel_info.cluster.cluster_role,
            cluster_hostname=kernel_info.cluster.cluster_hostname,
            session_id=UUID(kernel_info.session.session_id),
            image_reference=image_ref,
            architecture=architecture,
            status=KernelStatusGQL(kernel_info.lifecycle.status),
            status_changed=kernel_info.lifecycle.status_changed,
            status_info=kernel_info.lifecycle.status_info,
            status_data=kernel_info.lifecycle.status_data,
            created_at=kernel_info.lifecycle.created_at,
            terminated_at=kernel_info.lifecycle.terminated_at,
            starts_at=kernel_info.lifecycle.starts_at,
            scheduled_at=status_history.get(KernelStatus.SCHEDULED.name),
            agent_id=kernel_info.resource.agent if not hide_agents else None,
            agent_addr=kernel_info.resource.agent_addr if not hide_agents else None,
            container_id=kernel_info.resource.container_id if not hide_agents else None,
            resource_opts=kernel_info.resource.resource_opts,
            occupied_slots=JSONString.from_resource_slot(kernel_info.resource.occupied_slots),
            preopen_ports=kernel_info.network.preopen_ports,
        )


KernelEdge = Edge[KernelGQL]


@strawberry.type(description="Added in 26.1.0. Connection type for paginated kernel results.")
class KernelConnectionV2(Connection[KernelGQL]):
    count: int

    def __init__(self, *args, count: int, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
