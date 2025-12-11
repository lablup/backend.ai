"""GraphQL types for scaling group."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Optional, Self, override

import strawberry
from strawberry.relay import Node, NodeID
from strawberry.scalars import JSON

from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.data.scaling_group.types import (
    ScalingGroupData,
    ScalingGroupDriverConfig,
    ScalingGroupMetadata,
    ScalingGroupNetworkConfig,
    ScalingGroupSchedulerConfig,
    ScalingGroupSchedulerOptions,
    ScalingGroupStatus,
)
from ai.backend.manager.repositories.base import (
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.scaling_group.options import (
    ScalingGroupConditions,
    ScalingGroupOrders,
)

__all__ = (
    "ScalingGroupStatusGQL",
    "ScalingGroupMetadataGQL",
    "ScalingGroupNetworkConfigGQL",
    "ScalingGroupDriverConfigGQL",
    "ScalingGroupSchedulerOptionsGQL",
    "ScalingGroupSchedulerTypeGQL",
    "ScalingGroupSchedulerConfigGQL",
    "ScalingGroupV2GQL",
    "ScalingGroupFilterGQL",
    "ScalingGroupOrderByGQL",
    "ScalingGroupOrderFieldGQL",
)


@strawberry.type(
    name="ScalingGroupStatus",
    description="Added in 25.18.0. Status information for a scaling group",
)
class ScalingGroupStatusGQL:
    is_active: bool = strawberry.field(
        description=dedent_strip("""
            Whether the scaling group can accept new session creation requests.
            Inactive scaling groups are excluded from scheduling and cannot start new sessions.
        """)
    )
    is_public: bool = strawberry.field(
        description=dedent_strip("""
            Whether this scaling group is available for regular user sessions
            (interactive/batch/inference).
            When false, the scaling group is reserved for internal SYSTEM-type sessions only,
            such as management or infrastructure sessions.
        """)
    )

    @classmethod
    def from_dataclass(cls, data: ScalingGroupStatus) -> Self:
        return cls(
            is_active=data.is_active,
            is_public=data.is_public,
        )


@strawberry.type(
    name="ScalingGroupMetadata",
    description="Added in 25.18.0. Metadata information for a scaling group",
)
class ScalingGroupMetadataGQL:
    description: str = strawberry.field(
        description="Human-readable description of the scaling group's purpose"
    )
    created_at: datetime = strawberry.field(
        description="Timestamp when the scaling group was created"
    )

    @classmethod
    def from_dataclass(cls, data: ScalingGroupMetadata) -> Self:
        return cls(
            description=data.description,
            created_at=data.created_at,
        )


@strawberry.type(
    name="ScalingGroupNetworkConfig",
    description="Added in 25.18.0. Network configuration for a scaling group",
)
class ScalingGroupNetworkConfigGQL:
    wsproxy_addr: str = strawberry.field(
        description=dedent_strip("""
            App-proxy coordinator API server address.
            Manager uses this address to communicate with the app-proxy coordinator
            for managing service routes, endpoint registration, and proxying client connections
            to session services.
        """)
    )
    wsproxy_api_token: str = strawberry.field(
        description="Authentication token for the App-proxy coordinator API server."
    )
    use_host_network: bool = strawberry.field(
        description=dedent_strip("""
            Whether session containers use the host's network namespace
            instead of isolated container networking.
            Enables direct host port binding but reduces isolation.
        """)
    )

    @classmethod
    def from_dataclass(cls, data: ScalingGroupNetworkConfig) -> Self:
        return cls(
            wsproxy_addr=data.wsproxy_addr,
            wsproxy_api_token=data.wsproxy_api_token,
            use_host_network=data.use_host_network,
        )


@strawberry.type(
    name="ScalingGroupDriverConfig",
    description="Added in 25.18.0. Driver configuration for resource allocation",
)
class ScalingGroupDriverConfigGQL:
    name: str = strawberry.field(
        description=dedent_strip("""
            Agent resource driver implementation name.
            'static' uses a predefined set of agents registered to this scaling group.
        """)
    )
    options: JSON = strawberry.field(
        description="Driver-specific configuration options. Contents vary by driver type."
    )

    @classmethod
    def from_dataclass(cls, data: ScalingGroupDriverConfig) -> Self:
        return cls(
            name=data.name,
            options=data.options,
        )


@strawberry.type(
    name="ScalingGroupSchedulerOptions",
    description="Added in 25.18.0. Scheduler configuration options",
)
class ScalingGroupSchedulerOptionsGQL:
    allowed_session_types: list[str] = strawberry.field(
        description=dedent_strip("""
            Session types that can be scheduled in this scaling group.
            Valid values: 'interactive' , 'batch', 'inference'.
            Requests for unlisted types are rejected.
        """)
    )
    pending_timeout: float = strawberry.field(
        description=dedent_strip("""
            Maximum time in seconds a session can wait in PENDING state
            before automatic cancellation.
            Zero means no timeout.
            Used to prevent indefinite resource waiting when no agents are available.
        """)
    )
    config: JSON = strawberry.field(
        description=dedent_strip("""
            Scheduler-specific configuration options.
            Contents depend on the scheduler implementation (fifo/lifo/drf).
            Used for advanced scheduling behavior customization.
        """)
    )
    agent_selection_strategy: str = strawberry.field(
        description=dedent_strip("""
            Algorithm for selecting target agents when scheduling sessions.
            'dispersed' spreads sessions across available agents,
            'concentrated' packs sessions onto fewer agents,
            'roundrobin' cycles through agents sequentially.
        """)
    )
    agent_selector_config: JSON = strawberry.field(
        description=dedent_strip("""
            Configuration for the agent selection strategy.
            Structure varies by strategy - for example,
            concentrated strategy may specify endpoint spreading rules.
        """)
    )
    enforce_spreading_endpoint_replica: bool = strawberry.field(
        description=dedent_strip("""
            Whether inference service replicas should be distributed across different agents
            instead of co-locating on same agent.
            When true, forces replica spreading.
            Applied only when using concentrated agent selection strategy.
            Improves fault tolerance for model serving.
        """)
    )
    allow_fractional_resource_fragmentation: bool = strawberry.field(
        description=dedent_strip("""
            Whether agents accept session requests that allocate fractional resources
            (e.g., 0.5 GPU) causing resource fragmentation.
            When false, agents reject sessions that would prevent future efficient resource allocation.
        """)
    )
    route_cleanup_target_statuses: list[str] = strawberry.field(
        description=dedent_strip("""
            List of route health statuses that trigger automatic cleanup of service routes.
            Valid values: 'healthy', 'unhealthy', 'degraded'.
            Default: ['unhealthy'].
        """)
    )

    @classmethod
    def from_dataclass(cls, data: ScalingGroupSchedulerOptions) -> Self:
        return cls(
            allowed_session_types=[st.value for st in data.allowed_session_types],
            pending_timeout=data.pending_timeout.total_seconds(),
            config=data.config,
            agent_selection_strategy=data.agent_selection_strategy.value,
            agent_selector_config=data.agent_selector_config,
            enforce_spreading_endpoint_replica=data.enforce_spreading_endpoint_replica,
            allow_fractional_resource_fragmentation=data.allow_fractional_resource_fragmentation,
            route_cleanup_target_statuses=data.route_cleanup_target_statuses,
        )


@strawberry.enum(
    name="ScalingGroupSchedulerType",
    description=dedent_strip("""
        Added in 25.18.0. Scheduler type for session scheduling.

        - FIFO: First-In-First-Out - Schedules oldest pending sessions first
        - LIFO: Last-In-First-Out - Schedules newest pending sessions first
        - DRF: Dominant Resource Fairness - Balances resource usage across users
    """),
)
class ScalingGroupSchedulerTypeGQL(StrEnum):
    FIFO = "fifo"
    LIFO = "lifo"
    DRF = "drf"


@strawberry.type(
    name="ScalingGroupSchedulerConfig",
    description="Added in 25.18.0. Scheduler configuration for session scheduling",
)
class ScalingGroupSchedulerConfigGQL:
    name: ScalingGroupSchedulerTypeGQL = strawberry.field(
        description=dedent_strip("""
            Scheduling algorithm implementation.
            'fifo' schedules oldest pending sessions first,
            'lifo' schedules newest first,
            'drf' (Dominant Resource Fairness) balances resource usage across users.
        """)
    )
    options: ScalingGroupSchedulerOptionsGQL = strawberry.field(
        description=dedent_strip("""
            Detailed scheduler behavior configuration including session type restrictions,
            timeouts, agent selection strategy, and resource allocation policies.
        """)
    )

    @classmethod
    def from_dataclass(cls, data: ScalingGroupSchedulerConfig) -> Self:
        return cls(
            name=ScalingGroupSchedulerTypeGQL(data.name),
            options=ScalingGroupSchedulerOptionsGQL.from_dataclass(data.options),
        )


@strawberry.type(
    name="ScalingGroupV2",
    description="Added in 25.18.0. Scaling group with structured configuration",
)
class ScalingGroupV2GQL(Node):
    id: NodeID[str] = strawberry.field(
        description="Relay-style global node identifier for the scaling group"
    )
    name: str = strawberry.field(
        description=dedent_strip("""
            Unique name identifying the scaling group.
            Used as primary key and referenced by agents, sessions, and resource presets.
        """)
    )
    status: ScalingGroupStatusGQL = strawberry.field(
        description=dedent_strip("""
            Operational status controlling whether this scaling group accepts new sessions
            and its visibility to users without explicit access grants.
        """)
    )
    metadata: ScalingGroupMetadataGQL = strawberry.field(
        description=dedent_strip("""
            Administrative metadata including human-readable description
            and creation timestamp for audit and documentation purposes.
        """)
    )
    network: ScalingGroupNetworkConfigGQL = strawberry.field(
        description=dedent_strip("""
            Network configuration for connecting clients to interactive session services
            (terminals, notebooks, web apps) through WebSocket proxy infrastructure.
        """)
    )
    driver: ScalingGroupDriverConfigGQL = strawberry.field(
        description=dedent_strip("""
            Agent resource management driver determining how compute agents are provisioned
            and registered to this scaling group (static registration vs dynamic provisioning).
        """)
    )
    scheduler: ScalingGroupSchedulerConfigGQL = strawberry.field(
        description=dedent_strip("""
            Session scheduling configuration controlling queue management,
            agent selection strategy, resource allocation policies,
            and session lifecycle timeouts.
        """)
    )

    @classmethod
    def from_dataclass(cls, data: ScalingGroupData) -> Self:
        return cls(
            id=data.name,
            name=data.name,
            status=ScalingGroupStatusGQL.from_dataclass(data.status),
            metadata=ScalingGroupMetadataGQL.from_dataclass(data.metadata),
            network=ScalingGroupNetworkConfigGQL.from_dataclass(data.network),
            driver=ScalingGroupDriverConfigGQL.from_dataclass(data.driver),
            scheduler=ScalingGroupSchedulerConfigGQL.from_dataclass(data.scheduler),
        )


# Filter and OrderBy types


@strawberry.enum(name="ScalingGroupOrderField")
class ScalingGroupOrderFieldGQL(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"
    IS_ACTIVE = "is_active"
    IS_PUBLIC = "is_public"


@strawberry.input(
    name="ScalingGroupFilter",
    description="Added in 25.18.0. Filter for scaling groups",
)
class ScalingGroupFilterGQL(GQLFilter):
    name: Optional[StringFilter] = None
    description: Optional[StringFilter] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    driver: Optional[str] = None
    scheduler: Optional[str] = None
    use_host_network: Optional[bool] = None

    AND: Optional[list["ScalingGroupFilterGQL"]] = None
    OR: Optional[list["ScalingGroupFilterGQL"]] = None
    NOT: Optional[list["ScalingGroupFilterGQL"]] = None

    @override
    def build_conditions(self) -> list[QueryCondition]:
        """Build query conditions from this filter.

        Returns a list containing a single combined QueryCondition that represents
        all filters with proper logical operators applied.
        """
        # Collect direct field conditions (these will be combined with AND)
        field_conditions: list[QueryCondition] = []

        # Apply name filter
        if self.name:
            name_condition = self.name.build_query_condition(
                contains_factory=ScalingGroupConditions.by_name_contains,
                equals_factory=ScalingGroupConditions.by_name_equals,
            )
            if name_condition:
                field_conditions.append(name_condition)

        # Apply description filter
        if self.description:
            description_condition = self.description.build_query_condition(
                contains_factory=ScalingGroupConditions.by_description_contains,
                equals_factory=ScalingGroupConditions.by_description_equals,
            )
            if description_condition:
                field_conditions.append(description_condition)

        # Apply is_active filter
        if self.is_active is not None:
            field_conditions.append(ScalingGroupConditions.by_is_active(self.is_active))

        # Apply is_public filter
        if self.is_public is not None:
            field_conditions.append(ScalingGroupConditions.by_is_public(self.is_public))

        # Apply driver filter
        if self.driver:
            field_conditions.append(ScalingGroupConditions.by_driver(self.driver))

        # Apply scheduler filter
        if self.scheduler:
            field_conditions.append(ScalingGroupConditions.by_scheduler(self.scheduler))

        # Apply use_host_network filter
        if self.use_host_network is not None:
            field_conditions.append(
                ScalingGroupConditions.by_use_host_network(self.use_host_network)
            )

        # Handle AND logical operator - these are implicitly ANDed with field conditions
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


@strawberry.input(
    name="ScalingGroupOrderBy",
    description="Added in 25.18.0. Order by specification for scaling groups",
)
class ScalingGroupOrderByGQL(GQLOrderBy):
    field: ScalingGroupOrderFieldGQL
    direction: OrderDirection = OrderDirection.ASC

    @override
    def to_query_order(self) -> QueryOrder:
        """Convert to repository QueryOrder."""
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case ScalingGroupOrderFieldGQL.NAME:
                return ScalingGroupOrders.name(ascending)
            case ScalingGroupOrderFieldGQL.CREATED_AT:
                return ScalingGroupOrders.created_at(ascending)
            case ScalingGroupOrderFieldGQL.IS_ACTIVE:
                return ScalingGroupOrders.is_active(ascending)
            case ScalingGroupOrderFieldGQL.IS_PUBLIC:
                return ScalingGroupOrders.is_public(ascending)
