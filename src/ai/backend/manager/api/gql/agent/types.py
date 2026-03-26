from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Any, Self, cast

import strawberry
from strawberry import Info
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
    AgentStatusEnum,
    AgentStatusFilter,
)
from ai.backend.common.types import AgentId
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_added_field,
    gql_connection_type,
    gql_enum,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin, PydanticNodeMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.data.agent.types import AgentStatus

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


@gql_enum(
    BackendAIGQLMeta(added_version="26.1.0", description="Permissions related to agent operations"),
    name="AgentPermission",
)
class AgentPermissionGQL(StrEnum):
    READ_ATTRIBUTE = "read_attribute"
    UPDATE_ATTRIBUTE = "update_attribute"
    CREATE_COMPUTE_SESSION = "create_compute_session"
    CREATE_SERVICE = "create_service"


@gql_enum(
    BackendAIGQLMeta(added_version="26.1.0", description="Order by specification for agents"),
    name="AgentOrderField",
)
class AgentOrderFieldGQL(StrEnum):
    ID = "id"
    STATUS = "status"
    FIRST_CONTACT = "first_contact"
    SCALING_GROUP = "scaling_group"
    SCHEDULABLE = "schedulable"


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=dedent_strip("""
            Filter options for agent status within AgentFilter.
            It includes options to filter whether agent status is in a specific list or equals a specific value.
        """),
        added_version="24.09.0",
    ),
    name="AgentStatusFilter",
)
class AgentStatusFilterGQL(PydanticInputMixin[AgentStatusFilter]):
    in_: list[AgentStatusEnum] | None = gql_field(
        description="The in  field.", name="in", default=None
    )
    equals: AgentStatusEnum | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(description="Filter options for querying agents", added_version="26.1.0"),
    name="AgentFilter",
)
class AgentFilterGQL(PydanticInputMixin[AgentFilter]):
    id: StringFilter | None = None
    status: AgentStatusFilterGQL | None = None
    schedulable: bool | None = None
    scaling_group: StringFilter | None = None

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(description="Options for ordering agents", added_version="26.1.0"),
    name="AgentOrderBy",
)
class AgentOrderByGQL(PydanticInputMixin[AgentOrder]):
    field: AgentOrderFieldGQL
    direction: OrderDirection = OrderDirection.ASC


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.15.0",
        description="Hardware resource capacity, usage, and availability of an agent.",
    ),
    model=AgentResourceGQLDTO,
    name="AgentResource",
)
class AgentResourceGQL:
    capacity: JSON = gql_field(
        description="Total hardware resource capacity available on the agent. Expressed as a JSON object containing resource slots (e.g., cpu, mem, accelerators). Each slot represents the maximum amount of that resource type the agent can provide."
    )
    used: JSON = gql_field(
        description="Total amount of resources currently consumed by running and scheduled compute sessions. Includes both the requested resources for sessions being prepared and already allocated resources for active sessions. The sum of occupied resources across all session states that occupy agent resources (PREPARING, PULLING, RUNNING, RESTARTING, etc.). Expressed as a JSON object with the same structure as capacity."
    )
    free: JSON = gql_field(
        description="Available resources for scheduling new compute sessions (capacity - used). This represents the maximum resources that can be allocated to new sessions without exceeding the agent's capacity. Expressed as a JSON object with the same structure as capacity."
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
    total_resource: AgentResourceGQL = gql_field(
        description="Total resource capacity of the agent."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description="Status and lifecycle information for an agent.",
    ),
    model=AgentStatusInfoGQLDTO,
    name="AgentStatusInfo",
)
class AgentStatusInfoGQL:
    status: AgentStatus = gql_field(
        description="Current operational status of the agent. Indicates whether the agent is ALIVE (active and reachable), LOST (unreachable), TERMINATED (intentionally stopped), or RESTARTING (in recovery process)."
    )
    status_changed: datetime | None = gql_field(
        description="Timestamp when the agent last changed its status. Updated whenever the agent transitions between different status states (e.g., from ALIVE to LOST, or RESTARTING to ALIVE). Will be null if the agent status has never changed since initial registration."
    )
    first_contact: datetime | None = gql_field(
        description="Timestamp when the agent first registered with the manager. This value remains constant throughout the agent's lifecycle and can be used to track the agent's age or identify when it was initially deployed."
    )
    lost_at: datetime | None = gql_field(
        description="Timestamp when the agent was marked as lost or unreachable. Set when the manager detects the agent has stopped sending heartbeats. Will be null if the agent has never been lost or is currently alive."
    )
    schedulable: bool = gql_field(
        description="Indicates whether the agent is available for scheduling new compute sessions. An agent can be non-schedulable due to maintenance mode, resource constraints or other operational reasons by admin. When false, no new sessions will be assigned to this agent."
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

    entries: list[ComputePluginEntryGQL] = gql_field(
        description="List of compute plugins. Each entry contains a plugin name and its metadata. The list includes all accelerator and resource type plugins installed on the agent."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description="System and configuration information for an agent.",
    ),
    model=AgentSystemInfoGQLDTO,
    name="AgentSystemInfo",
)
class AgentSystemInfoGQL:
    architecture: str = gql_field(
        description='Hardware architecture of the agent\'s host system (e.g., "x86_64", "aarch64"). Used to match compute sessions with compatible container images and ensure proper binary execution on the agent.'
    )
    version: str = gql_field(
        description='Version string of the Backend.AI agent software running on this node. Follows semantic versioning (e.g., "26.1.0") and helps identify compatibility and available features.'
    )
    auto_terminate_abusing_kernel: bool = gql_field(
        description="Legacy configuration flag, no longer actively used in the system. Retained for backward compatibility and schema consistency. Originally intended to control automatic termination of misbehaving sessions."
    )
    compute_plugins: ComputePluginsGQL = gql_field(
        description="List of compute plugin metadata supported by this agent. Each plugin represents a specific accelerator or resource type (e.g., CUDA). Entries contain plugin names and their associated metadata with plugin-specific configuration and capabilities."
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
    id: NodeID[str]
    resource_info: AgentResourceGQL = gql_field(
        description="Hardware resource capacity, usage, and availability information. Contains capacity (total), used (occupied by sessions), and free (available) resource slots including CPU cores, memory, accelerators (GPUs, TPUs), and other compute resources."
    )
    status_info: AgentStatusInfoGQL = gql_field(
        description="Current operational status and lifecycle timestamps. Includes the agent's status (ALIVE, LOST, etc.), status change history, initial registration time, and schedulability state."
    )
    system_info: AgentSystemInfoGQL = gql_field(
        description="System configuration and software version information. Contains the host architecture, agent software version, and available compute plugins for accelerators and specialized hardware."
    )
    network_info: AgentNetworkInfoGQL = gql_field(
        description="Network location and connectivity information. Provides the agent's region and network address for manager-to-agent communication."
    )
    permissions: list[AgentPermissionGQL] = gql_field(
        description="List of permissions the current authenticated user has on this agent. Determines which operations (read attributes, create sessions, etc.) the user can perform on this specific agent based on RBAC policies."
    )
    scaling_group: str = gql_field(
        description="Name of the scaling group this agent belongs to. Scaling groups are logical collections of agents used for resource scheduling, quota management, and workload isolation across different user groups or projects."
    )

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.1.0", description="Load the container count for this agent."
        )
    )  # type: ignore[misc]
    async def container_count(
        self,
        info: Info[StrawberryGQLContext],
    ) -> int:
        """
        Get the container count for a specific agent.
        """
        return await info.context.data_loaders.container_count_loader.load(AgentId(self.id))

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.2.0",
            description="List of kernels running on this agent with pagination support.",
        )
    )  # type: ignore[misc]
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
            AgentId(self.id),
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

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.3.0",
            description="List of sessions running on this agent with pagination support.",
        )
    )  # type: ignore[misc]
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
            AgentId(self.id),
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

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.3.0",
            description="Per-slot resource capacity and usage for this agent.",
        )
    )  # type: ignore[misc]
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

        agent_id = str(self.id)
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
                used=Decimal(item.used),
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
        return cast(list[Self | None], results)


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
