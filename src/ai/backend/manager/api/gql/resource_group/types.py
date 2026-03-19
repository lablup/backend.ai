"""GraphQL types for resource group."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any, Self, assert_never

import strawberry
from strawberry import Info
from strawberry.relay import NodeID

from ai.backend.common.dto.manager.v2.resource_group.request import (
    PreemptionConfigInputDTO,
)
from ai.backend.common.dto.manager.v2.resource_group.request import (
    ResourceGroupFilter as ResourceGroupFilterDTO,
)
from ai.backend.common.dto.manager.v2.resource_group.request import (
    ResourceGroupOrder as ResourceGroupOrderDTO,
)
from ai.backend.common.dto.manager.v2.resource_group.request import (
    UpdateResourceGroupConfigInput as UpdateResourceGroupConfigInputDTO,
)
from ai.backend.common.dto.manager.v2.resource_group.request import (
    UpdateResourceGroupFairShareSpecInput as UpdateResourceGroupFairShareSpecInputDTO,
)
from ai.backend.common.dto.manager.v2.resource_group.response import (
    PreemptionConfigInfo,
)
from ai.backend.common.dto.manager.v2.resource_group.types import (
    ResourceGroupOrderDirection as ResourceGroupOrderDirectionEnum,
)
from ai.backend.common.dto.manager.v2.resource_group.types import (
    ResourceGroupOrderField as ResourceGroupOrderFieldEnum,
)
from ai.backend.common.types import PreemptionMode, PreemptionOrder
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_node_type,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.fair_share.types.common import (
    ResourceSlotGQL,
    ResourceWeightEntryGQL,
    ResourceWeightEntryInputGQL,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.data.scaling_group.types import (
    PreemptionConfig as DataPreemptionConfig,
)
from ai.backend.manager.data.scaling_group.types import (
    ResourceInfo,
    ScalingGroupData,
    SchedulerType,
)
from ai.backend.manager.models.scaling_group.types import FairShareScalingGroupSpec
from ai.backend.manager.services.scaling_group.actions.get_resource_info import (
    GetResourceInfoAction,
)

__all__ = (
    "FairShareScalingGroupSpecGQL",
    "PreemptionConfigGQL",
    "PreemptionConfigInput",
    "PreemptionModeGQL",
    "PreemptionOrderGQL",
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
    "UpdateResourceGroupInput",
    "UpdateResourceGroupPayload",
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


@strawberry.enum(
    name="PreemptionMode",
    description="Added in 26.3.0. How to preempt a session when preemption is triggered.",
)
class PreemptionModeGQL(StrEnum):
    """Preemption mode enumeration for GraphQL."""

    TERMINATE = "terminate"
    RESCHEDULE = "reschedule"

    @classmethod
    def from_preemption_mode(cls, mode: PreemptionMode) -> PreemptionModeGQL:
        """Convert from internal PreemptionMode to GQL type."""
        match mode:
            case PreemptionMode.TERMINATE:
                return cls.TERMINATE
            case PreemptionMode.RESCHEDULE:
                return cls.RESCHEDULE
            case _:
                assert_never(mode)


@strawberry.enum(
    name="PreemptionOrder",
    description="Added in 26.3.0. Tie-breaking order for same-priority sessions during preemption.",
)
class PreemptionOrderGQL(StrEnum):
    """Preemption order enumeration for GraphQL."""

    OLDEST = "oldest"
    NEWEST = "newest"

    @classmethod
    def from_preemption_order(cls, order: PreemptionOrder) -> PreemptionOrderGQL:
        """Convert from internal PreemptionOrder to GQL type."""
        match order:
            case PreemptionOrder.OLDEST:
                return cls.OLDEST
            case PreemptionOrder.NEWEST:
                return cls.NEWEST
            case _:
                assert_never(order)


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Preemption configuration for a resource group.",
    ),
    model=PreemptionConfigInfo,
    name="PreemptionConfig",
)
class PreemptionConfigGQL:
    """Preemption configuration for GraphQL."""

    preemptible_priority: strawberry.auto
    order: PreemptionOrderGQL
    mode: PreemptionModeGQL

    @classmethod
    def from_dataclass(cls, data: DataPreemptionConfig) -> Self:
        """Convert from data layer PreemptionConfig to GQL type."""
        return cls(
            preemptible_priority=data.preemptible_priority,
            order=PreemptionOrderGQL.from_preemption_order(data.order),
            mode=PreemptionModeGQL.from_preemption_mode(data.mode),
        )


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Status information for a resource group.",
    ),
    name="ResourceGroupStatus",
)
class ResourceGroupStatusGQL:
    """Status information for a resource group."""

    is_active: bool = strawberry.field(
        description="Whether the resource group is active and can accept new sessions."
    )
    is_public: bool = strawberry.field(
        description="Whether the resource group is publicly accessible to all users."
    )


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Metadata for a resource group.",
    ),
    name="ResourceGroupMetadata",
)
class ResourceGroupMetadataGQL:
    """Metadata for a resource group."""

    description: str | None = strawberry.field(
        description="Human-readable description of the resource group."
    )
    created_at: datetime = strawberry.field(
        description="Timestamp when the resource group was created."
    )


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Network configuration for a resource group.",
    ),
    name="ResourceGroupNetworkConfig",
)
class ResourceGroupNetworkConfigGQL:
    """Network configuration for a resource group."""

    wsproxy_addr: str | None = strawberry.field(
        description="WebSocket proxy address for this resource group."
    )
    use_host_network: bool = strawberry.field(
        description="Whether to use host network mode for containers in this resource group."
    )


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Scheduler configuration for a resource group.",
    ),
    name="ResourceGroupSchedulerConfig",
)
class ResourceGroupSchedulerConfigGQL:
    """Scheduler configuration for a resource group."""

    type: SchedulerTypeGQL = strawberry.field(
        description="Type of scheduler used for session scheduling (fifo, lifo, drf, fair-share)."
    )
    preemption: PreemptionConfigGQL = strawberry.field(
        description="Added in 26.3.0. Preemption configuration for this resource group."
    )


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description=(
            "Fair share calculation configuration for a resource group. "
            "Defines parameters for computing fair share factors across domains, projects, and users."
        ),
    ),
    name="FairShareScalingGroupSpec",
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
    resource_weights: list[ResourceWeightEntryGQL] = strawberry.field(
        description=(
            "Added in 26.2.0. Weights for each resource type with default indicators. "
            "All resource types from capacity are included. "
            "Shows which resources use explicit vs default weights."
        )
    )

    @classmethod
    def from_model(
        cls,
        spec: FairShareScalingGroupSpec,
        uses_default_resources: frozenset[str],
    ) -> Self:
        """Convert from Pydantic model to GQL type.

        Args:
            spec: FairShareScalingGroupSpec with merged resource_weights
            uses_default_resources: Set of resource types using default weight
        """
        # Convert ResourceSlot to list[ResourceWeightEntryGQL]
        weight_entries = [
            ResourceWeightEntryGQL(
                resource_type=resource_type,
                weight=weight,
                uses_default=resource_type in uses_default_resources,
            )
            for resource_type, weight in spec.resource_weights.items()
        ]

        return cls(
            half_life_days=spec.half_life_days,
            lookback_days=spec.lookback_days,
            decay_unit_days=spec.decay_unit_days,
            default_weight=spec.default_weight,
            resource_weights=weight_entries,
        )


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description=(
            "Resource information for a resource group. "
            "Provides aggregated resource metrics including capacity, used, and free resources."
        ),
    ),
    name="ResourceInfo",
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
            capacity=ResourceSlotGQL.from_slot_quantities(info.capacity),
            used=ResourceSlotGQL.from_slot_quantities(info.used),
            free=ResourceSlotGQL.from_slot_quantities(info.free),
        )


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description="Resource group with structured configuration",
    ),
    name="ResourceGroup",
)
class ResourceGroupGQL(PydanticNodeMixin[Any]):
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

    # Private field to store original fair share spec for lazy loading
    _fair_share_spec_data: strawberry.Private[FairShareScalingGroupSpec]

    @classmethod
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.resource_group_loader.load_many(node_ids)
        return [cls.from_dataclass(data) if data is not None else None for data in results]

    @classmethod
    def from_pydantic(
        cls,
        dto: ScalingGroupData,
        extra: dict[str, Any] | None = None,
        *,
        id_field: str = "id",
    ) -> Self:
        return cls(
            id=dto.name,
            name=dto.name,
            status=ResourceGroupStatusGQL(
                is_active=dto.status.is_active,
                is_public=dto.status.is_public,
            ),
            metadata=ResourceGroupMetadataGQL(
                description=dto.metadata.description if dto.metadata.description else None,
                created_at=dto.metadata.created_at,
            ),
            network=ResourceGroupNetworkConfigGQL(
                wsproxy_addr=dto.network.wsproxy_addr if dto.network.wsproxy_addr else None,
                use_host_network=dto.network.use_host_network,
            ),
            scheduler=ResourceGroupSchedulerConfigGQL(
                type=SchedulerTypeGQL.from_scheduler_type(dto.scheduler.name),
                preemption=PreemptionConfigGQL.from_dataclass(dto.scheduler.options.preemption),
            ),
            _fair_share_spec_data=dto.fair_share_spec,
        )

    @classmethod
    def from_dataclass(cls, data: ScalingGroupData) -> Self:
        return cls.from_pydantic(data)

    @strawberry.field(  # type: ignore[misc]
        description=(
            "Added in 26.1.0. Fair share calculation configuration for this resource group. "
            "Defines decay parameters and resource weights for fair share factor computation. "
            "Resource weights are merged with capacity and include default indicators."
        )
    )
    async def fair_share_spec(
        self, info: Info[StrawberryGQLContext, None]
    ) -> FairShareScalingGroupSpecGQL:
        """Get fair share spec with merged resource weights from capacity.

        This is a lazy-loaded field that merges the resource group's fair share spec
        with its current capacity to provide complete resource weight information.
        """
        from ai.backend.common.types import ResourceSlot

        ctx = info.context

        # Get capacity from resource info
        action = GetResourceInfoAction(scaling_group=self.name)
        result = await ctx.processors.scaling_group.get_resource_info.wait_for_complete(action)
        capacity = result.resource_info.capacity

        # Merge resource weights with capacity
        merged = {}
        uses_default = []

        capacity_keys = {sq.slot_name for sq in capacity}
        for resource_type in capacity_keys:
            if resource_type in self._fair_share_spec_data.resource_weights.data:
                merged[resource_type] = self._fair_share_spec_data.resource_weights.data[
                    resource_type
                ]
            else:
                merged[resource_type] = self._fair_share_spec_data.default_weight
                uses_default.append(resource_type)

        # Create merged spec
        merged_spec = FairShareScalingGroupSpec(
            half_life_days=self._fair_share_spec_data.half_life_days,
            lookback_days=self._fair_share_spec_data.lookback_days,
            decay_unit_days=self._fair_share_spec_data.decay_unit_days,
            default_weight=self._fair_share_spec_data.default_weight,
            resource_weights=ResourceSlot(merged),
        )

        return FairShareScalingGroupSpecGQL.from_model(merged_spec, frozenset(uses_default))

    @strawberry.field(  # type: ignore[misc]
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
    CREATED_AT = "created_at"
    IS_ACTIVE = "is_active"


@strawberry.experimental.pydantic.input(
    model=ResourceGroupFilterDTO,
    name="ResourceGroupFilter",
    description="Added in 26.1.0. Filter for resource groups",
)
class ResourceGroupFilterGQL:
    name: StringFilter | None = None
    description: StringFilter | None = None
    is_active: bool | None = None
    is_public: bool | None = None

    AND: list[ResourceGroupFilterGQL] | None = None
    OR: list[ResourceGroupFilterGQL] | None = None
    NOT: list[ResourceGroupFilterGQL] | None = None

    def to_pydantic(self) -> ResourceGroupFilterDTO:
        return ResourceGroupFilterDTO(
            name=self.name.to_pydantic() if self.name else None,
            description=self.description.to_pydantic() if self.description else None,
            is_active=self.is_active,
            is_public=self.is_public,
            AND=[f.to_pydantic() for f in self.AND] if self.AND else None,
            OR=[f.to_pydantic() for f in self.OR] if self.OR else None,
            NOT=[f.to_pydantic() for f in self.NOT] if self.NOT else None,
        )


@strawberry.experimental.pydantic.input(
    model=ResourceGroupOrderDTO,
    name="ResourceGroupOrderBy",
    description="Added in 26.1.0. Order by specification for resource groups",
)
class ResourceGroupOrderByGQL:
    field: ResourceGroupOrderFieldGQL
    direction: OrderDirection = OrderDirection.ASC

    def to_pydantic(self) -> ResourceGroupOrderDTO:
        return ResourceGroupOrderDTO(
            field=ResourceGroupOrderFieldEnum(self.field.value),
            direction=ResourceGroupOrderDirectionEnum(self.direction.value.lower()),
        )


@strawberry.experimental.pydantic.input(
    model=PreemptionConfigInputDTO,
    name="PreemptionConfigInput",
    description="Added in 26.3.0. Input for preemption configuration.",
)
class PreemptionConfigInput:
    """Input for preemption configuration. Replaces entire preemption config when provided."""

    preemptible_priority: int = strawberry.field(
        default=5,
        description=("Sessions with priority <= this value are preemptible. Default is 5."),
    )
    order: PreemptionOrderGQL = strawberry.field(
        default=PreemptionOrderGQL.OLDEST,
        description=(
            "Tie-breaking order for same-priority sessions (OLDEST, NEWEST). Default is OLDEST."
        ),
    )
    mode: PreemptionModeGQL = strawberry.field(
        default=PreemptionModeGQL.TERMINATE,
        description=("How to preempt sessions (TERMINATE, RESCHEDULE). Default is TERMINATE."),
    )


# Mutation Input/Payload types


@strawberry.experimental.pydantic.input(
    model=UpdateResourceGroupFairShareSpecInputDTO,
    name="UpdateResourceGroupFairShareSpecInput",
    description=(
        "Added in 26.1.0. Input for updating resource group fair share configuration. "
        "All fields are optional - only provided fields will be updated, others retain existing values."
    ),
)
class UpdateResourceGroupFairShareSpecInput:
    """Partial update input for fair share spec. All fields optional for partial update."""

    resource_group_name: str = strawberry.field(description="Name of the resource group to update.")
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

    def to_pydantic(self) -> UpdateResourceGroupFairShareSpecInputDTO:
        return UpdateResourceGroupFairShareSpecInputDTO(
            resource_group_name=self.resource_group_name,
            half_life_days=self.half_life_days,
            lookback_days=self.lookback_days,
            decay_unit_days=self.decay_unit_days,
            default_weight=self.default_weight,
            resource_weights=None
            if self.resource_weights is None
            else [entry.to_pydantic() for entry in self.resource_weights],
        )


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description="Payload for resource group fair share spec update mutation.",
    ),
    name="UpdateResourceGroupFairShareSpecPayload",
)
class UpdateResourceGroupFairShareSpecPayload:
    """Payload for fair share spec update mutation."""

    resource_group: ResourceGroupGQL = strawberry.field(
        description="The updated resource group with new fair share configuration."
    )


@strawberry.experimental.pydantic.input(
    model=UpdateResourceGroupConfigInputDTO,
    name="UpdateResourceGroupInput",
    description=(
        "Added in 26.2.0. Resource group configuration update input. "
        "All fields are optional - only provided fields will be updated. "
        "Supports all ScalingGroupUpdaterSpec fields (except fair_share, use separate mutation)."
    ),
)
class UpdateResourceGroupInput:
    """Input for updating resource group configuration. All fields optional for partial update."""

    resource_group_name: str = strawberry.field(description="Name of the resource group to update.")

    # Status fields (ScalingGroupStatusUpdaterSpec)
    is_active: bool | None = strawberry.field(
        default=None,
        description="Whether the resource group is active. Leave null to keep existing value.",
    )
    is_public: bool | None = strawberry.field(
        default=None,
        description="Whether the resource group is public. Leave null to keep existing value.",
    )

    # Metadata fields (ScalingGroupMetadataUpdaterSpec)
    description: str | None = strawberry.field(
        default=None,
        description="Human-readable description. Leave null to keep existing value.",
    )

    # Network config fields (ScalingGroupNetworkConfigUpdaterSpec)
    app_proxy_addr: str | None = strawberry.field(
        default=None,
        description="App proxy address. Leave null to keep existing value.",
    )
    appproxy_api_token: str | None = strawberry.field(
        default=None,
        description="App proxy API token. Leave null to keep existing value.",
    )
    use_host_network: bool | None = strawberry.field(
        default=None,
        description="Whether to use host network mode. Leave null to keep existing value.",
    )

    # Scheduler config fields (ScalingGroupSchedulerConfigUpdaterSpec)
    scheduler_type: SchedulerTypeGQL | None = strawberry.field(
        default=None,
        description=(
            "Scheduler type (FIFO, LIFO, DRF, FAIR_SHARE). Leave null to keep existing value."
        ),
    )
    preemption: PreemptionConfigInput | None = strawberry.field(
        default=None,
        description=(
            "Added in 26.3.0. Preemption configuration. When provided, replaces the entire "
            "preemption config. Leave null to keep existing value."
        ),
    )

    def to_pydantic(self) -> UpdateResourceGroupConfigInputDTO:
        return UpdateResourceGroupConfigInputDTO(
            resource_group_name=self.resource_group_name,
            is_active=self.is_active,
            is_public=self.is_public,
            description=self.description,
            app_proxy_addr=self.app_proxy_addr,
            appproxy_api_token=self.appproxy_api_token,
            use_host_network=self.use_host_network,
            scheduler_type=self.scheduler_type,
            preemption=None if self.preemption is None else self.preemption.to_pydantic(),
        )


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Payload for resource group update mutation.",
    ),
    name="UpdateResourceGroupPayload",
)
class UpdateResourceGroupPayload:
    """Payload for resource group update mutation."""

    resource_group: ResourceGroupGQL = strawberry.field(
        description="The updated resource group with new configuration."
    )
