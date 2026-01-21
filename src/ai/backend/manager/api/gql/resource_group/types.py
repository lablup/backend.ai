"""GraphQL types for resource group."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from enum import StrEnum
from typing import Any, Self, override

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
    "AgentSelectorConfigGQL",
    "SchedulerConfigGQL",
    "ResourceGroupDriverConfigGQL",
    "ResourceGroupFilterGQL",
    "ResourceGroupMetadataGQL",
    "ResourceGroupNetworkConfigGQL",
    "ResourceGroupOrderByGQL",
    "ResourceGroupOrderFieldGQL",
    "ResourceGroupSchedulerConfigGQL",
    "ResourceGroupSchedulerOptionsGQL",
    "ResourceGroupSchedulerTypeGQL",
    "ResourceGroupStatusGQL",
    "ResourceGroupGQL",
)


@strawberry.type(
    name="ResourceGroupStatus",
    description="Added in 25.18.0. Status information for a resource group",
)
class ResourceGroupStatusGQL:
    is_active: bool = strawberry.field(
        description=dedent_strip("""
            Whether the resource group can accept new session creation requests.
            Inactive resource groups are excluded from scheduling and cannot start new sessions.
        """)
    )
    is_public: bool = strawberry.field(
        description=dedent_strip("""
            Whether this resource group is available for regular user sessions
            (interactive/batch/inference).
            When false, the resource group is reserved for internal SYSTEM-type sessions only,
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
    name="ResourceGroupMetadata",
    description="Added in 25.18.0. Metadata information for a resource group",
)
class ResourceGroupMetadataGQL:
    description: str = strawberry.field(
        description="Human-readable description of the resource group's purpose"
    )
    created_at: datetime = strawberry.field(
        description="Timestamp when the resource group was created"
    )

    @classmethod
    def from_dataclass(cls, data: ScalingGroupMetadata) -> Self:
        return cls(
            description=data.description,
            created_at=data.created_at,
        )


@strawberry.type(
    name="ResourceGroupNetworkConfig",
    description="Added in 25.18.0. Network configuration for a resource group",
)
class ResourceGroupNetworkConfigGQL:
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
    name="ResourceGroupDriverConfig",
    description="Added in 26.1.0. Driver configuration for resource allocation",
)
class ResourceGroupDriverConfigGQL:
    name: str = strawberry.field(
        description=dedent_strip("""
            Agent resource driver implementation name.
            'static' uses a predefined set of agents registered to this resource group.
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
    name="SchedulerConfig",
    description="Added in 26.1.0. Scheduler-specific configuration options",
)
class SchedulerConfigGQL:
    num_retries_to_skip: int = strawberry.field(
        description=dedent_strip("""
            Number of scheduling retries to skip before attempting to schedule a session.
            Used to prevent repeated scheduling attempts for sessions that previously failed.
        """)
    )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> Self:
        return cls(
            num_retries_to_skip=data.get("num_retries_to_skip", 0),
        )


@strawberry.type(
    name="AgentSelectorConfig",
    description="Added in 26.1.0. Configuration for the agent selection strategy",
)
class AgentSelectorConfigGQL:
    kernel_counts_at_same_endpoint: int = strawberry.field(
        description=dedent_strip("""
            Number of existing kernels already running on the same endpoint.
            Used by the concentrated agent selection strategy when enforce_spreading_endpoint_replica is enabled.

            When enforce_spreading_endpoint_replica is true, inference service replicas are distributed
            across different agents for improved fault tolerance. This count helps the scheduler
            avoid placing new replicas on agents that already host replicas for the same endpoint,
            ensuring better distribution of model serving workloads.
        """)
    )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> Self:
        return cls(
            kernel_counts_at_same_endpoint=data.get("kernel_counts_at_same_endpoint", 0),
        )


@strawberry.type(
    name="ResourceGroupSchedulerOptions",
    description="Added in 25.18.0. Scheduler configuration options",
)
class ResourceGroupSchedulerOptionsGQL:
    allowed_session_types: list[str] = strawberry.field(
        description=dedent_strip("""
            Session types that can be scheduled in this resource group.
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
    config: SchedulerConfigGQL = strawberry.field(
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
    agent_selector_config: AgentSelectorConfigGQL = strawberry.field(
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
            config=SchedulerConfigGQL.from_mapping(data.config),
            agent_selection_strategy=data.agent_selection_strategy.value,
            agent_selector_config=AgentSelectorConfigGQL.from_mapping(data.agent_selector_config),
            enforce_spreading_endpoint_replica=data.enforce_spreading_endpoint_replica,
            allow_fractional_resource_fragmentation=data.allow_fractional_resource_fragmentation,
            route_cleanup_target_statuses=data.route_cleanup_target_statuses,
        )


@strawberry.enum(
    name="ResourceGroupSchedulerType",
    description=dedent_strip("""
        Added in 25.18.0. Scheduler type for session scheduling.

        - FIFO: First-In-First-Out - Schedules oldest pending sessions first
        - LIFO: Last-In-First-Out - Schedules newest pending sessions first
        - DRF: Dominant Resource Fairness - Balances resource usage across users
    """),
)
class ResourceGroupSchedulerTypeGQL(StrEnum):
    FIFO = "fifo"
    LIFO = "lifo"
    DRF = "drf"


@strawberry.type(
    name="ResourceGroupSchedulerConfig",
    description="Added in 25.18.0. Scheduler configuration for session scheduling",
)
class ResourceGroupSchedulerConfigGQL:
    name: ResourceGroupSchedulerTypeGQL = strawberry.field(
        description=dedent_strip("""
            Scheduling algorithm implementation.
            'fifo' schedules oldest pending sessions first,
            'lifo' schedules newest first,
            'drf' (Dominant Resource Fairness) balances resource usage across users.
        """)
    )
    options: ResourceGroupSchedulerOptionsGQL = strawberry.field(
        description=dedent_strip("""
            Detailed scheduler behavior configuration including session type restrictions,
            timeouts, agent selection strategy, and resource allocation policies.
        """)
    )

    @classmethod
    def from_dataclass(cls, data: ScalingGroupSchedulerConfig) -> Self:
        return cls(
            name=ResourceGroupSchedulerTypeGQL(data.name),
            options=ResourceGroupSchedulerOptionsGQL.from_dataclass(data.options),
        )


@strawberry.type(
    name="ResourceGroup",
    description="Added in 25.18.0. Resource group with structured configuration",
)
class ResourceGroupGQL(Node):
    id: NodeID[str] = strawberry.field(
        description="Relay-style global node identifier for the resource group"
    )
    name: str = strawberry.field(
        description=dedent_strip("""
            Unique name identifying the resource group.
            Used as primary key and referenced by agents, sessions, and resource presets.
        """)
    )
    status: ResourceGroupStatusGQL = strawberry.field(
        description=dedent_strip("""
            Operational status controlling whether this resource group accepts new sessions
            and its visibility to users without explicit access grants.
        """)
    )
    metadata: ResourceGroupMetadataGQL = strawberry.field(
        description=dedent_strip("""
            Administrative metadata including human-readable description
            and creation timestamp for audit and documentation purposes.
        """)
    )
    network: ResourceGroupNetworkConfigGQL = strawberry.field(
        description=dedent_strip("""
            Network configuration for connecting clients to interactive session services
            (terminals, notebooks, web apps) through WebSocket proxy infrastructure.
        """)
    )
    scheduler: ResourceGroupSchedulerConfigGQL = strawberry.field(
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
            status=ResourceGroupStatusGQL.from_dataclass(data.status),
            metadata=ResourceGroupMetadataGQL.from_dataclass(data.metadata),
            network=ResourceGroupNetworkConfigGQL.from_dataclass(data.network),
            scheduler=ResourceGroupSchedulerConfigGQL.from_dataclass(data.scheduler),
        )


# Filter and OrderBy types


@strawberry.enum(name="ResourceGroupOrderField")
class ResourceGroupOrderFieldGQL(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"
    IS_ACTIVE = "is_active"
    IS_PUBLIC = "is_public"


@strawberry.input(
    name="ResourceGroupFilter",
    description="Added in 25.18.0. Filter for resource groups",
)
class ResourceGroupFilterGQL(GQLFilter):
    name: StringFilter | None = None
    description: StringFilter | None = None
    is_active: bool | None = None
    is_public: bool | None = None
    scheduler: str | None = None
    use_host_network: bool | None = None

    AND: list[ResourceGroupFilterGQL] | None = None
    OR: list[ResourceGroupFilterGQL] | None = None
    NOT: list[ResourceGroupFilterGQL] | None = None

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
                starts_with_factory=ScalingGroupConditions.by_name_starts_with,
                ends_with_factory=ScalingGroupConditions.by_name_ends_with,
            )
            if name_condition:
                field_conditions.append(name_condition)

        # Apply description filter
        if self.description:
            description_condition = self.description.build_query_condition(
                contains_factory=ScalingGroupConditions.by_description_contains,
                equals_factory=ScalingGroupConditions.by_description_equals,
                starts_with_factory=ScalingGroupConditions.by_description_starts_with,
                ends_with_factory=ScalingGroupConditions.by_description_ends_with,
            )
            if description_condition:
                field_conditions.append(description_condition)

        # Apply is_active filter
        if self.is_active is not None:
            field_conditions.append(ScalingGroupConditions.by_is_active(self.is_active))

        # Apply is_public filter
        if self.is_public is not None:
            field_conditions.append(ScalingGroupConditions.by_is_public(self.is_public))

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
    name="ResourceGroupOrderBy",
    description="Added in 25.18.0. Order by specification for resource groups",
)
class ResourceGroupOrderByGQL(GQLOrderBy):
    field: ResourceGroupOrderFieldGQL
    direction: OrderDirection = OrderDirection.ASC

    @override
    def to_query_order(self) -> QueryOrder:
        """Convert to repository QueryOrder."""
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case ResourceGroupOrderFieldGQL.NAME:
                return ScalingGroupOrders.name(ascending)
            case ResourceGroupOrderFieldGQL.CREATED_AT:
                return ScalingGroupOrders.created_at(ascending)
            case ResourceGroupOrderFieldGQL.IS_ACTIVE:
                return ScalingGroupOrders.is_active(ascending)
            case ResourceGroupOrderFieldGQL.IS_PUBLIC:
                return ScalingGroupOrders.is_public(ascending)
