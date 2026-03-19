from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Any, Self

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, NodeID
from strawberry.scalars import JSON

from ai.backend.common.dto.manager.v2.agent.request import AgentFilter, AgentOrder
from ai.backend.common.dto.manager.v2.agent.response import (
    AgentNetworkInfoGQLDTO,
    AgentNode,
    AgentResourceGQLDTO,
    AgentStatsGQLDTO,
    AgentStatusInfoGQLDTO,  # used as pydantic model for AgentStatusInfoGQL
    AgentSystemInfoGQLDTO,
    ComputePluginEntryDTO,
    ComputePluginsGQLDTO,
)
from ai.backend.common.dto.manager.v2.agent.types import (
    AgentOrderField,
    AgentStatusEnum,
    AgentStatusFilter,
)
from ai.backend.common.dto.manager.v2.agent.types import (
    OrderDirection as OrderDirectionDTO,
)
from ai.backend.common.types import AgentId
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_connection_type,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.data.agent.types import AgentDetailData, AgentStatus
from ai.backend.manager.models.rbac.permission_defs import AgentPermission

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.kernel.types import (
        KernelV2ConnectionGQL,
        KernelV2FilterGQL,
        KernelV2OrderByGQL,
    )
    from ai.backend.manager.api.gql.resource_slot.types import (
        AgentResourceConnectionGQL,
        AgentResourceSlotFilterGQL,
        AgentResourceSlotOrderByGQL,
    )
    from ai.backend.manager.api.gql.session.types import (
        SessionV2ConnectionGQL,
        SessionV2FilterGQL,
        SessionV2OrderByGQL,
    )


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
    STATUS = "status"
    FIRST_CONTACT = "first_contact"
    SCALING_GROUP = "scaling_group"
    SCHEDULABLE = "schedulable"


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="24.09.0"),
    model=AgentStatusFilter,
    name="AgentStatusFilter",
    description=dedent_strip("""
        Added in 26.1.0. Filter options for agent status within AgentFilter.
        It includes options to filter whether agent status is in a specific list or equals a specific value.
    """),
)
class AgentStatusFilterGQL:
    in_: list[AgentStatus] | None = strawberry.field(name="in", default=None)
    equals: AgentStatus | None = None

    def to_pydantic(self) -> AgentStatusFilter:
        return AgentStatusFilter(
            in_=[AgentStatusEnum(s.name) for s in self.in_] if self.in_ else None,
            equals=AgentStatusEnum(self.equals.name) if self.equals else None,
        )


@strawberry.input(
    name="AgentFilter",
    description="Added in 26.1.0. Filter options for querying agents",
)
class AgentFilterGQL:
    id: StringFilter | None = None
    status: AgentStatusFilterGQL | None = None
    schedulable: bool | None = None
    scaling_group: StringFilter | None = None

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None

    def to_pydantic(self) -> AgentFilter:
        return AgentFilter(
            id=self.id.to_pydantic() if self.id else None,
            status=self.status.to_pydantic() if self.status else None,
            schedulable=self.schedulable,
            resource_group=self.scaling_group.to_pydantic() if self.scaling_group else None,
            AND=[f.to_pydantic() for f in self.AND] if self.AND else None,
            OR=[f.to_pydantic() for f in self.OR] if self.OR else None,
            NOT=[f.to_pydantic() for f in self.NOT] if self.NOT else None,
        )


@gql_pydantic_input(
    BackendAIGQLMeta(description="Options for ordering agents", added_version="26.1.0"),
    model=AgentOrder,
    name="AgentOrderBy",
)
class AgentOrderByGQL:
    field: AgentOrderFieldGQL
    direction: OrderDirection = OrderDirection.ASC

    def to_pydantic(self) -> AgentOrder:
        ascending = self.direction == OrderDirection.ASC
        dto_direction = OrderDirectionDTO.ASC if ascending else OrderDirectionDTO.DESC
        match self.field:
            case AgentOrderFieldGQL.ID:
                return AgentOrder(field=AgentOrderField.ID, direction=dto_direction)
            case AgentOrderFieldGQL.STATUS:
                return AgentOrder(field=AgentOrderField.STATUS, direction=dto_direction)
            case AgentOrderFieldGQL.FIRST_CONTACT:
                return AgentOrder(field=AgentOrderField.FIRST_CONTACT, direction=dto_direction)
            case AgentOrderFieldGQL.SCALING_GROUP:
                return AgentOrder(field=AgentOrderField.RESOURCE_GROUP, direction=dto_direction)
            case AgentOrderFieldGQL.SCHEDULABLE:
                return AgentOrder(field=AgentOrderField.SCHEDULABLE, direction=dto_direction)


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.15.0",
        description="Hardware resource capacity, usage, and availability of an agent.",
    ),
    model=AgentResourceGQLDTO,
    name="AgentResource",
)
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


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.15.0",
        description="Aggregated resource statistics for an agent.",
    ),
    model=AgentStatsGQLDTO,
    name="AgentStats",
)
class AgentStatsGQL:
    total_resource: AgentResourceGQL = strawberry.field(description="Added in 25.15.0")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description="Status and lifecycle information for an agent.",
    ),
    model=AgentStatusInfoGQLDTO,
    name="AgentStatusInfo",
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


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description="A single compute plugin entry representing one plugin and its metadata.",
    ),
    model=ComputePluginEntryDTO,
    name="ComputePluginEntry",
)
class ComputePluginEntryGQL:
    """Single compute plugin entry with plugin name and metadata."""

    plugin_name: strawberry.auto
    value: strawberry.auto


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description=(
            "A collection of compute plugins available on an agent. "
            "Each entry specifies a plugin name and its associated metadata."
        ),
    ),
    model=ComputePluginsGQLDTO,
    name="ComputePlugins",
)
class ComputePluginsGQL:
    """Compute plugins container with multiple plugin entries."""

    entries: list[ComputePluginEntryGQL] = strawberry.field(
        description=(
            "List of compute plugins. Each entry contains a plugin name and its metadata. "
            "The list includes all accelerator and resource type plugins installed on the agent."
        )
    )

    @classmethod
    def from_mapping(cls, plugins: Mapping[str, str]) -> ComputePluginsGQL:
        """Convert a mapping of plugin name to value to GraphQL type."""
        entries = [
            ComputePluginEntryGQL(plugin_name=name, value=value) for name, value in plugins.items()
        ]
        return cls(entries=entries)


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description="System and configuration information for an agent.",
    ),
    model=AgentSystemInfoGQLDTO,
    name="AgentSystemInfo",
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
    compute_plugins: ComputePluginsGQL = strawberry.field(
        description=dedent_strip("""
            List of compute plugin metadata supported by this agent.
            Each plugin represents a specific accelerator or resource type (e.g., CUDA).
            Entries contain plugin names and their associated metadata with
            plugin-specific configuration and capabilities.
        """)
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description="Network-related information for an agent.",
    ),
    model=AgentNetworkInfoGQLDTO,
    name="AgentNetworkInfo",
)
class AgentNetworkInfoGQL:
    region: strawberry.auto
    addr: strawberry.auto


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description="Strawberry-based Agent type replacing AgentNode.",
    ),
    name="AgentV2",
)
class AgentV2GQL(PydanticNodeMixin[AgentNode]):
    _agent_id: strawberry.Private[AgentId]
    id: NodeID[str]
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

    @strawberry.field(description="Added in 26.1.0. Load the container count for this agent.")  # type: ignore[misc]
    async def container_count(
        self,
        info: Info[StrawberryGQLContext],
    ) -> int:
        """
        Get the container count for a specific agent.
        """
        return await info.context.data_loaders.container_count_loader.load(self._agent_id)

    @strawberry.field(  # type: ignore[misc]
        description="Added in 26.2.0. List of kernels running on this agent with pagination support."
    )
    async def kernels(
        self,
        info: Info[StrawberryGQLContext],
        filter: Annotated[
            KernelV2FilterGQL, strawberry.lazy("ai.backend.manager.api.gql.kernel.types")
        ]
        | None = None,
        order_by: list[
            Annotated[
                KernelV2OrderByGQL, strawberry.lazy("ai.backend.manager.api.gql.kernel.types")
            ]
        ]
        | None = None,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Annotated[
        KernelV2ConnectionGQL, strawberry.lazy("ai.backend.manager.api.gql.kernel.types")
    ]:
        """Fetch kernels associated with this agent."""
        from ai.backend.common.dto.manager.v2.kernel.request import AdminSearchKernelsInput
        from ai.backend.manager.api.gql.base import encode_cursor
        from ai.backend.manager.api.gql.kernel.types import KernelV2ConnectionGQL, KernelV2EdgeGQL

        payload = await info.context.adapters.session.search_kernels_by_agent(
            self._agent_id,
            AdminSearchKernelsInput(
                filter=filter.to_pydantic() if filter else None,
                order=[o.to_pydantic() for o in order_by] if order_by else None,
                first=first,
                after=after,
                last=last,
                before=before,
                limit=limit,
                offset=offset,
            ),
        )
        from ai.backend.manager.api.gql.kernel.types import KernelV2GQL

        nodes = [KernelV2GQL.from_pydantic(node) for node in payload.items]
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

    @strawberry.field(  # type: ignore[misc]
        description="Added in 26.3.0. List of sessions running on this agent with pagination support."
    )
    async def sessions(
        self,
        info: Info[StrawberryGQLContext],
        filter: Annotated[
            SessionV2FilterGQL, strawberry.lazy("ai.backend.manager.api.gql.session.types")
        ]
        | None = None,
        order_by: list[
            Annotated[
                SessionV2OrderByGQL, strawberry.lazy("ai.backend.manager.api.gql.session.types")
            ]
        ]
        | None = None,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Annotated[
        SessionV2ConnectionGQL, strawberry.lazy("ai.backend.manager.api.gql.session.types")
    ]:
        """Fetch sessions associated with this agent."""
        from ai.backend.common.dto.manager.v2.session.request import AdminSearchSessionsInput
        from ai.backend.manager.api.gql.base import encode_cursor
        from ai.backend.manager.api.gql.session.types import (
            SessionV2ConnectionGQL,
            SessionV2EdgeGQL,
            SessionV2GQL,
        )

        payload = await info.context.adapters.session.search_sessions_by_agent(
            self._agent_id,
            AdminSearchSessionsInput(
                filter=filter.to_pydantic() if filter else None,
                order=[o.to_pydantic() for o in order_by] if order_by else None,
                first=first,
                after=after,
                last=last,
                before=before,
                limit=limit,
                offset=offset,
            ),
        )
        nodes = [SessionV2GQL.from_pydantic(node) for node in payload.items]
        edges = [SessionV2EdgeGQL(node=node, cursor=encode_cursor(node.id)) for node in nodes]
        return SessionV2ConnectionGQL(
            edges=edges,
            page_info=strawberry.relay.PageInfo(
                has_next_page=payload.has_next_page,
                has_previous_page=payload.has_previous_page,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
            count=payload.total_count,
        )

    @strawberry.field(  # type: ignore[misc]
        description="Added in 26.3.0. Per-slot resource capacity and usage for this agent."
    )
    async def resource_slots(
        self,
        info: Info[StrawberryGQLContext],
        filter: Annotated[
            AgentResourceSlotFilterGQL,
            strawberry.lazy("ai.backend.manager.api.gql.resource_slot.types"),
        ]
        | None = None,
        order_by: list[
            Annotated[
                AgentResourceSlotOrderByGQL,
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
        AgentResourceConnectionGQL,
        strawberry.lazy("ai.backend.manager.api.gql.resource_slot.types"),
    ]:
        """Fetch per-slot resource capacity and usage for this agent."""
        from decimal import Decimal

        import strawberry as _strawberry

        from ai.backend.common.dto.manager.query import StringFilter as StringFilterDTO
        from ai.backend.common.dto.manager.v2.resource_slot.request import (
            AdminSearchAgentResourcesInput,
        )
        from ai.backend.common.dto.manager.v2.resource_slot.request import (
            AgentResourceFilter as AgentResourceFilterDTO,
        )
        from ai.backend.common.dto.manager.v2.resource_slot.request import (
            AgentResourceOrder as AgentResourceOrderDTO,
        )
        from ai.backend.manager.api.gql.base import encode_cursor
        from ai.backend.manager.api.gql.resource_slot.types import (
            AgentResourceConnectionGQL,
            AgentResourceSlotEdgeGQL,
            AgentResourceSlotGQL,
        )

        agent_id = str(self._agent_id)
        pydantic_filter: AgentResourceFilterDTO | None = None
        if filter is not None:
            pydantic_filter = filter.to_pydantic()
            if pydantic_filter.agent_id is None:
                pydantic_filter = AgentResourceFilterDTO(
                    slot_name=pydantic_filter.slot_name,
                    agent_id=StringFilterDTO(equals=agent_id),
                    AND=pydantic_filter.AND,
                    OR=pydantic_filter.OR,
                    NOT=pydantic_filter.NOT,
                )
        else:
            pydantic_filter = AgentResourceFilterDTO(
                agent_id=StringFilterDTO(equals=agent_id),
            )

        pydantic_order: list[AgentResourceOrderDTO] | None = (
            [o.to_pydantic() for o in order_by] if order_by is not None else None
        )

        search_input = AdminSearchAgentResourcesInput(
            filter=pydantic_filter,
            order=pydantic_order,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
        payload = await info.context.adapters.resource_slot.search_agent_resources(search_input)

        edges = []
        for item in payload.items:
            slot_name = item.slot_name
            node = AgentResourceSlotGQL(
                id=_strawberry.ID(item.id),
                slot_name=slot_name,
                capacity=Decimal(item.capacity),
                used=Decimal(item.occupied),
            )
            cursor = encode_cursor(slot_name)
            edges.append(AgentResourceSlotEdgeGQL(node=node, cursor=cursor))

        return AgentResourceConnectionGQL(
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
        results = await info.context.data_loaders.agent_loader.load_many([
            AgentId(nid) for nid in node_ids
        ])
        return [cls.from_agent_detail_data(data) if data is not None else None for data in results]

    @classmethod
    def from_agent_detail_data(cls, detail_data: AgentDetailData) -> Self:
        data = detail_data.agent

        return cls(
            _agent_id=data.id,
            id=ID(data.id),
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
                compute_plugins=ComputePluginsGQL.from_mapping(data.compute_plugins),
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

    @classmethod
    def from_pydantic(
        cls,
        dto: AgentNode,
        extra: dict[str, Any] | None = None,
        *,
        id_field: str = "id",
    ) -> Self:
        return cls(
            _agent_id=AgentId(dto.id),
            id=ID(dto.id),
            resource_info=AgentResourceGQL(
                capacity=dto.resource_info.capacity,
                used=dto.resource_info.used,
                free=dto.resource_info.free,
            ),
            status_info=AgentStatusInfoGQL(
                status=AgentStatus(dto.status_info.status),
                status_changed=dto.status_info.status_changed,
                first_contact=dto.status_info.first_contact,
                lost_at=dto.status_info.lost_at,
                schedulable=dto.status_info.schedulable,
            ),
            system_info=AgentSystemInfoGQL(
                architecture=dto.system_info.architecture,
                version=dto.system_info.version,
                auto_terminate_abusing_kernel=False,
                compute_plugins=(
                    ComputePluginsGQL.from_mapping(dto.system_info.compute_plugins)
                    if dto.system_info.compute_plugins is not None
                    else ComputePluginsGQL(entries=[])
                ),
            ),
            network_info=AgentNetworkInfoGQL(
                region=dto.network_info.region,
                addr=dto.network_info.addr,
            ),
            permissions=[AgentPermissionGQL(p) for p in dto.permissions],
            scaling_group=dto.scaling_group,
        )


AgentV2Edge = Edge[AgentV2GQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description="Relay-style connection type for paginated lists of agents.",
    ),
)
class AgentV2Connection(Connection[AgentV2GQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
