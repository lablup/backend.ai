"""GraphQL types for resource group."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Self, override

import strawberry
from strawberry import Info
from strawberry.relay import Node, NodeID

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.fair_share.types.common import (
    ResourceSlotGQL,
    ResourceWeightEntryInputGQL,
)
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.data.scaling_group.types import (
    ResourceInfo,
    ScalingGroupData,
    SchedulerType,
)
from ai.backend.manager.models.scaling_group.types import FairShareScalingGroupSpec
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
from ai.backend.manager.services.scaling_group.actions.get_resource_info import (
    GetResourceInfoAction,
)

__all__ = (
    "FairShareScalingGroupSpecGQL",
    "ResourceGroupFilterGQL",
    "ResourceGroupGQL",
    "ResourceGroupMetadataGQL",
    "ResourceGroupNetworkConfigGQL",
    "ResourceGroupOrderByGQL",
    "ResourceGroupOrderFieldGQL",
    "ResourceGroupSchedulerConfigGQL",
    "ResourceGroupStatusGQL",
    "ResourceInfoGQL",
    "SchedulerTypeGQL",
    "UpdateResourceGroupFairShareSpecInput",
    "UpdateResourceGroupFairShareSpecPayload",
)


@strawberry.enum(
    name="SchedulerType",
    description="Added in 26.2.0. Type of scheduler used for session scheduling in a resource group.",
)
class SchedulerTypeGQL(StrEnum):
    """Scheduler type enumeration for GraphQL."""

    FIFO = "fifo"
    LIFO = "lifo"
    DRF = "drf"
    FAIR_SHARE = "fair-share"

    @classmethod
    def from_scheduler_type(cls, scheduler_type: SchedulerType) -> SchedulerTypeGQL:
        """Convert from data layer SchedulerType to GQL type."""
        match scheduler_type:
            case SchedulerType.FIFO:
                return cls.FIFO
            case SchedulerType.LIFO:
                return cls.LIFO
            case SchedulerType.DRF:
                return cls.DRF
            case SchedulerType.FAIR_SHARE:
                return cls.FAIR_SHARE


@strawberry.type(
    name="ResourceGroupStatus",
    description="Added in 26.2.0. Status information for a resource group.",
)
class ResourceGroupStatusGQL:
    """Status information for a resource group."""

    is_active: bool = strawberry.field(
        description="Whether the resource group is active and can accept new sessions."
    )
    is_public: bool = strawberry.field(
        description="Whether the resource group is publicly accessible to all users."
    )


@strawberry.type(
    name="ResourceGroupMetadata",
    description="Added in 26.2.0. Metadata for a resource group.",
)
class ResourceGroupMetadataGQL:
    """Metadata for a resource group."""

    description: str | None = strawberry.field(
        description="Human-readable description of the resource group."
    )
    created_at: datetime = strawberry.field(
        description="Timestamp when the resource group was created."
    )


@strawberry.type(
    name="ResourceGroupNetworkConfig",
    description="Added in 26.2.0. Network configuration for a resource group.",
)
class ResourceGroupNetworkConfigGQL:
    """Network configuration for a resource group."""

    wsproxy_addr: str | None = strawberry.field(
        description="WebSocket proxy address for this resource group."
    )
    use_host_network: bool = strawberry.field(
        description="Whether to use host network mode for containers in this resource group."
    )


@strawberry.type(
    name="ResourceGroupSchedulerConfig",
    description="Added in 26.2.0. Scheduler configuration for a resource group.",
)
class ResourceGroupSchedulerConfigGQL:
    """Scheduler configuration for a resource group."""

    type: SchedulerTypeGQL = strawberry.field(
        description="Type of scheduler used for session scheduling (fifo, lifo, drf, fair-share)."
    )


@strawberry.type(
    name="FairShareScalingGroupSpec",
    description=(
        "Added in 26.1.0. Fair share calculation configuration for a resource group. "
        "Defines parameters for computing fair share factors across domains, projects, and users."
    ),
)
class FairShareScalingGroupSpecGQL:
    """Fair share configuration for a resource group."""

    half_life_days: int = strawberry.field(
        description=(
            "Half-life for exponential decay in days. "
            "Determines how quickly historical usage loses significance. "
            "Default is 7 days."
        )
    )
    lookback_days: int = strawberry.field(
        description=(
            "Total lookback period in days for usage aggregation. "
            "Only usage within this window is considered. "
            "Default is 28 days."
        )
    )
    decay_unit_days: int = strawberry.field(
        description=(
            "Granularity of decay buckets in days. "
            "Usage is aggregated into buckets of this size. "
            "Default is 1 day."
        )
    )
    default_weight: Decimal = strawberry.field(
        description=(
            "Default weight for entities without explicit weight in this resource group. "
            "Default is 1.0."
        )
    )
    resource_weights: ResourceSlotGQL = strawberry.field(
        description=(
            "Weights for each resource type when calculating normalized usage. "
            "If a resource type is not specified, default weight (1.0) is used."
        )
    )

    @classmethod
    def from_model(cls, spec: FairShareScalingGroupSpec) -> Self:
        """Convert from Pydantic model to GQL type."""
        return cls(
            half_life_days=spec.half_life_days,
            lookback_days=spec.lookback_days,
            decay_unit_days=spec.decay_unit_days,
            default_weight=spec.default_weight,
            resource_weights=ResourceSlotGQL.from_resource_slot(spec.resource_weights),
        )


@strawberry.type(
    name="ResourceInfo",
    description=(
        "Added in 26.1.0. Resource information for a resource group. "
        "Provides aggregated resource metrics including capacity, used, and free resources."
    ),
)
class ResourceInfoGQL:
    """Resource information containing capacity, used, and free resource metrics."""

    capacity: ResourceSlotGQL = strawberry.field(
        description=(
            "Total available resources from ALIVE, schedulable agents in this resource group."
        )
    )
    used: ResourceSlotGQL = strawberry.field(
        description=(
            "Currently occupied resources from active kernels (RUNNING/TERMINATING status)."
        )
    )
    free: ResourceSlotGQL = strawberry.field(description="Available resources (capacity - used).")

    @classmethod
    def from_resource_info(cls, info: ResourceInfo) -> Self:
        """Convert from ResourceInfo dataclass to GQL type."""
        return cls(
            capacity=ResourceSlotGQL.from_resource_slot(info.capacity),
            used=ResourceSlotGQL.from_resource_slot(info.used),
            free=ResourceSlotGQL.from_resource_slot(info.free),
        )


@strawberry.type(
    name="ResourceGroup",
    description="Added in 26.1.0. Resource group with structured configuration",
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
        description="Added in 26.2.0. Status information including active and public flags."
    )
    metadata: ResourceGroupMetadataGQL = strawberry.field(
        description="Added in 26.2.0. Metadata including description and creation timestamp."
    )
    network: ResourceGroupNetworkConfigGQL = strawberry.field(
        description="Added in 26.2.0. Network configuration for the resource group."
    )
    scheduler: ResourceGroupSchedulerConfigGQL = strawberry.field(
        description=(
            "Added in 26.2.0. Scheduler configuration for the resource group. "
            "Use scheduler.type to check if fair-share scheduling is enabled."
        )
    )
    fair_share_spec: FairShareScalingGroupSpecGQL = strawberry.field(
        description=(
            "Added in 26.1.0. Fair share calculation configuration for this resource group. "
            "Defines decay parameters and resource weights for fair share factor computation."
        )
    )

    @classmethod
    def from_dataclass(cls, data: ScalingGroupData) -> Self:
        return cls(
            id=data.name,
            name=data.name,
            status=ResourceGroupStatusGQL(
                is_active=data.status.is_active,
                is_public=data.status.is_public,
            ),
            metadata=ResourceGroupMetadataGQL(
                description=data.metadata.description if data.metadata.description else None,
                created_at=data.metadata.created_at,
            ),
            network=ResourceGroupNetworkConfigGQL(
                wsproxy_addr=data.network.wsproxy_addr if data.network.wsproxy_addr else None,
                use_host_network=data.network.use_host_network,
            ),
            scheduler=ResourceGroupSchedulerConfigGQL(
                type=SchedulerTypeGQL.from_scheduler_type(data.scheduler.name),
            ),
            fair_share_spec=FairShareScalingGroupSpecGQL.from_model(data.fair_share_spec),
        )

    @strawberry.field(
        description=(
            "Added in 26.1.0. Resource usage information for this resource group. "
            "Provides aggregated metrics for capacity, used, and free resources. "
            "This is a lazy-loaded field that queries agent and kernel data on demand."
        )
    )
    async def resource_info(self, info: Info[StrawberryGQLContext, None]) -> ResourceInfoGQL:
        """Get resource information for this resource group."""
        ctx = info.context
        action = GetResourceInfoAction(scaling_group=self.name)
        result = await ctx.processors.scaling_group.get_resource_info.wait_for_complete(action)
        return ResourceInfoGQL.from_resource_info(result.resource_info)


# Filter and OrderBy types


@strawberry.enum(
    name="ResourceGroupOrderField",
    description="Added in 26.1.0. Fields available for ordering resource groups",
)
class ResourceGroupOrderFieldGQL(StrEnum):
    NAME = "name"


@strawberry.input(
    name="ResourceGroupFilter",
    description="Added in 26.1.0. Filter for resource groups",
)
class ResourceGroupFilterGQL(GQLFilter):
    name: StringFilter | None = None

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
    description="Added in 26.1.0. Order by specification for resource groups",
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


# Mutation Input/Payload types


@strawberry.input(
    name="UpdateResourceGroupFairShareSpecInput",
    description=(
        "Added in 26.1.0. Input for updating resource group fair share configuration. "
        "All fields are optional - only provided fields will be updated, others retain existing values."
    ),
)
class UpdateResourceGroupFairShareSpecInput:
    """Partial update input for fair share spec. All fields optional for partial update."""

    resource_group: str = strawberry.field(description="Name of the resource group to update.")
    half_life_days: int | None = strawberry.field(
        default=None,
        description="Half-life for exponential decay in days. Leave null to keep existing value.",
    )
    lookback_days: int | None = strawberry.field(
        default=None,
        description="Total lookback period in days. Leave null to keep existing value.",
    )
    decay_unit_days: int | None = strawberry.field(
        default=None,
        description="Granularity of decay buckets in days. Leave null to keep existing value.",
    )
    default_weight: Decimal | None = strawberry.field(
        default=None,
        description="Default weight for entities. Leave null to keep existing value.",
    )
    resource_weights: list[ResourceWeightEntryInputGQL] | None = strawberry.field(
        default=None,
        description=(
            "Resource weights for fair share calculation. "
            "Each entry specifies a resource type and its weight multiplier. "
            "Only provided resource types are updated (partial update). "
            "Set weight to null to remove that resource type (revert to default). "
            "Leave the entire list null to keep all existing values."
        ),
    )

    def merge_with(self, existing: FairShareScalingGroupSpec) -> FairShareScalingGroupSpec:
        """Merge partial input with existing spec, returning a new complete spec."""
        # Merge resource_weights: partial update with deletion support
        merged_resource_weights = existing.resource_weights
        if self.resource_weights is not None:
            # Start with existing weights
            merged_weights_dict = dict(existing.resource_weights)
            for entry in self.resource_weights:
                if entry.weight is None:
                    # Remove the resource type (revert to default)
                    merged_weights_dict.pop(entry.resource_type, None)
                else:
                    # Update or add the resource type
                    merged_weights_dict[entry.resource_type] = entry.weight
            merged_resource_weights = ResourceSlot(merged_weights_dict)

        return FairShareScalingGroupSpec(
            half_life_days=self.half_life_days
            if self.half_life_days is not None
            else existing.half_life_days,
            lookback_days=self.lookback_days
            if self.lookback_days is not None
            else existing.lookback_days,
            decay_unit_days=self.decay_unit_days
            if self.decay_unit_days is not None
            else existing.decay_unit_days,
            default_weight=self.default_weight
            if self.default_weight is not None
            else existing.default_weight,
            resource_weights=merged_resource_weights,
        )


@strawberry.type(
    name="UpdateResourceGroupFairShareSpecPayload",
    description="Added in 26.1.0. Payload for resource group fair share spec update mutation.",
)
class UpdateResourceGroupFairShareSpecPayload:
    """Payload for fair share spec update mutation."""

    resource_group: ResourceGroupGQL = strawberry.field(
        description="The updated resource group with new fair share configuration."
    )
