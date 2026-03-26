"""GraphQL types for resource group."""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from enum import StrEnum
from typing import Self

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
    FairShareScalingGroupSpecInfo,
    PreemptionConfigInfo,
    ResourceGroupDetailNode,
    ResourceGroupMetadataInfo,
    ResourceGroupNetworkConfigInfo,
    ResourceGroupSchedulerConfigInfo,
    ResourceGroupStatusInfo,
    ResourceInfoNode,
    UpdateResourceGroupConfigPayloadNode,
    UpdateResourceGroupFairShareSpecPayloadNode,
)
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_added_field,
    gql_enum,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.fair_share.types.common import (
    ResourceSlotGQL,
    ResourceWeightEntryGQL,
    ResourceWeightEntryInputGQL,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin, PydanticOutputMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext

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


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Type of scheduler used for session scheduling in a resource group.",
    ),
    name="SchedulerType",
)
class SchedulerTypeGQL(StrEnum):
    """Scheduler type enumeration for GraphQL."""

    FIFO = "fifo"
    LIFO = "lifo"
    DRF = "drf"
    FAIR_SHARE = "fair-share"


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="How to preempt a session when preemption is triggered.",
    ),
    name="PreemptionMode",
)
class PreemptionModeGQL(StrEnum):
    """Preemption mode enumeration for GraphQL."""

    TERMINATE = "terminate"
    RESCHEDULE = "reschedule"


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Tie-breaking order for same-priority sessions during preemption.",
    ),
    name="PreemptionOrder",
)
class PreemptionOrderGQL(StrEnum):
    """Preemption order enumeration for GraphQL."""

    OLDEST = "oldest"
    NEWEST = "newest"


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Preemption configuration for a resource group.",
    ),
    model=PreemptionConfigInfo,
    name="PreemptionConfig",
)
class PreemptionConfigGQL(PydanticOutputMixin[PreemptionConfigInfo]):
    """Preemption configuration for GraphQL."""

    preemptible_priority: int = gql_field(
        description="Sessions with priority <= this value are eligible for preemption."
    )
    order: PreemptionOrderGQL = gql_field(
        description="Tie-breaking order for same-priority sessions during preemption."
    )
    mode: PreemptionModeGQL = gql_field(
        description="How to preempt a session when preemption is triggered."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0", description="Status information for a resource group."
    ),
    model=ResourceGroupStatusInfo,
    all_fields=True,
    name="ResourceGroupStatus",
)
class ResourceGroupStatusGQL(PydanticOutputMixin[ResourceGroupStatusInfo]):
    pass


@gql_pydantic_type(
    BackendAIGQLMeta(added_version="26.2.0", description="Metadata for a resource group."),
    model=ResourceGroupMetadataInfo,
    all_fields=True,
    name="ResourceGroupMetadata",
)
class ResourceGroupMetadataGQL(PydanticOutputMixin[ResourceGroupMetadataInfo]):
    pass


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0", description="Network configuration for a resource group."
    ),
    model=ResourceGroupNetworkConfigInfo,
    all_fields=True,
    name="ResourceGroupNetworkConfig",
)
class ResourceGroupNetworkConfigGQL(PydanticOutputMixin[ResourceGroupNetworkConfigInfo]):
    pass


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0", description="Scheduler configuration for a resource group."
    ),
    model=ResourceGroupSchedulerConfigInfo,
    name="ResourceGroupSchedulerConfig",
)
class ResourceGroupSchedulerConfigGQL(PydanticOutputMixin[ResourceGroupSchedulerConfigInfo]):
    """Scheduler configuration for a resource group."""

    type: SchedulerTypeGQL = gql_field(
        description="Type of scheduler used for session scheduling (fifo, lifo, drf, fair-share)."
    )
    preemption: PreemptionConfigGQL = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.3.0", description="Preemption configuration for this resource group."
        )
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description=(
            "Fair share calculation configuration for a resource group. "
            "Defines parameters for computing fair share factors across domains, projects, and users."
        ),
    ),
    model=FairShareScalingGroupSpecInfo,
    name="FairShareScalingGroupSpec",
)
class FairShareScalingGroupSpecGQL(PydanticOutputMixin[FairShareScalingGroupSpecInfo]):
    """Fair share configuration for a resource group."""

    half_life_days: int = gql_field(
        description="Half-life for exponential decay in days. Determines how quickly historical usage loses significance. Default is 7 days."
    )
    lookback_days: int = gql_field(
        description="Total lookback period in days for usage aggregation. Only usage within this window is considered. Default is 28 days."
    )
    decay_unit_days: int = gql_field(
        description="Granularity of decay buckets in days. Usage is aggregated into buckets of this size. Default is 1 day."
    )
    default_weight: Decimal = gql_field(
        description="Default weight for entities without explicit weight in this resource group. Default is 1.0."
    )
    resource_weights: list[ResourceWeightEntryGQL] = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.2.0",
            description="Weights for each resource type with default indicators. All resource types from capacity are included. Shows which resources use explicit vs default weights.",
        )
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description=(
            "Resource information for a resource group. "
            "Provides aggregated resource metrics including capacity, used, and free resources."
        ),
    ),
    model=ResourceInfoNode,
    name="ResourceInfo",
)
class ResourceInfoGQL(PydanticOutputMixin[ResourceInfoNode]):
    """Resource information containing capacity, used, and free resource metrics."""

    capacity: ResourceSlotGQL = gql_field(
        description="Total available resources from ALIVE, schedulable agents in this resource group."
    )
    used: ResourceSlotGQL = gql_field(
        description="Currently occupied resources from active kernels (RUNNING/TERMINATING status)."
    )
    free: ResourceSlotGQL = gql_field(description="Available resources (capacity - used).")


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description="Resource group with structured configuration",
    ),
    name="ResourceGroup",
)
class ResourceGroupGQL(PydanticNodeMixin[ResourceGroupDetailNode]):
    id: NodeID[str] = gql_field(
        description="Relay-style global node identifier for the resource group"
    )
    name: str = gql_field(
        description="Unique name identifying the resource group. Used as primary key and referenced by agents, sessions, and resource presets."
    )
    status: ResourceGroupStatusGQL = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.2.0",
            description="Status information including active and public flags.",
        )
    )
    metadata: ResourceGroupMetadataGQL = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.2.0",
            description="Metadata including description and creation timestamp.",
        )
    )
    network: ResourceGroupNetworkConfigGQL = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.2.0", description="Network configuration for the resource group."
        )
    )
    scheduler: ResourceGroupSchedulerConfigGQL = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.2.0",
            description="Scheduler configuration for the resource group. Use scheduler.type to check if fair-share scheduling is enabled.",
        )
    )

    @classmethod
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[ResourceGroupGQL | None]:
        return await info.context.data_loaders.resource_group_loader.load_many(node_ids)

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.1.0",
            description="Fair share calculation configuration for this resource group. Defines decay parameters and resource weights for fair share factor computation. Resource weights are merged with capacity and include default indicators.",
        )
    )  # type: ignore[misc]
    async def fair_share_spec(
        self, info: Info[StrawberryGQLContext, None]
    ) -> FairShareScalingGroupSpecGQL:
        """Get fair share spec with merged resource weights from capacity."""
        ctx = info.context
        dto = await ctx.adapters.resource_group.get_fair_share_spec(self.name)
        return FairShareScalingGroupSpecGQL.from_pydantic(dto)

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.1.0",
            description="Resource usage information for this resource group. Provides aggregated metrics for capacity, used, and free resources. This is a lazy-loaded field that queries agent and kernel data on demand.",
        )
    )  # type: ignore[misc]
    async def resource_info(self, info: Info[StrawberryGQLContext, None]) -> ResourceInfoGQL:
        """Get resource information for this resource group."""
        ctx = info.context
        resource_info_dto = await ctx.adapters.resource_group.get_resource_info(self.name)
        return ResourceInfoGQL.from_pydantic(resource_info_dto)


# Filter and OrderBy types


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.1.0", description="Fields available for ordering resource groups"
    ),
    name="ResourceGroupOrderField",
)
class ResourceGroupOrderFieldGQL(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"
    IS_ACTIVE = "is_active"


@gql_pydantic_input(
    BackendAIGQLMeta(description="Filter for resource groups", added_version="26.1.0"),
    name="ResourceGroupFilter",
)
class ResourceGroupFilterGQL(PydanticInputMixin[ResourceGroupFilterDTO]):
    name: StringFilter | None = None
    description: StringFilter | None = None
    is_active: bool | None = None
    is_public: bool | None = None

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Order by specification for resource groups", added_version="26.1.0"
    ),
    name="ResourceGroupOrderBy",
)
class ResourceGroupOrderByGQL(PydanticInputMixin[ResourceGroupOrderDTO]):
    field: ResourceGroupOrderFieldGQL
    direction: OrderDirection = OrderDirection.ASC


@gql_pydantic_input(
    BackendAIGQLMeta(description="Input for preemption configuration.", added_version="26.3.0"),
    name="PreemptionConfigInput",
)
class PreemptionConfigInput(PydanticInputMixin[PreemptionConfigInputDTO]):
    """Input for preemption configuration. Replaces entire preemption config when provided."""

    preemptible_priority: int = gql_field(
        description="Sessions with priority <= this value are preemptible. Default is 5.", default=5
    )
    order: PreemptionOrderGQL = gql_field(
        description="Tie-breaking order for same-priority sessions (OLDEST, NEWEST). Default is OLDEST.",
        default=PreemptionOrderGQL.OLDEST,
    )
    mode: PreemptionModeGQL = gql_field(
        description="How to preempt sessions (TERMINATE, RESCHEDULE). Default is TERMINATE.",
        default=PreemptionModeGQL.TERMINATE,
    )


# Mutation Input/Payload types


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for updating resource group fair share configuration. All fields are optional - only provided fields will be updated, others retain existing values.",
        added_version="26.1.0",
    ),
    name="UpdateResourceGroupFairShareSpecInput",
)
class UpdateResourceGroupFairShareSpecInput(
    PydanticInputMixin[UpdateResourceGroupFairShareSpecInputDTO]
):
    """Partial update input for fair share spec. All fields optional for partial update."""

    resource_group_name: str = gql_field(description="Name of the resource group to update.")
    half_life_days: int | None = gql_field(
        description="Half-life for exponential decay in days. Leave null to keep existing value.",
        default=None,
    )
    lookback_days: int | None = gql_field(
        description="Total lookback period in days. Leave null to keep existing value.",
        default=None,
    )
    decay_unit_days: int | None = gql_field(
        description="Granularity of decay buckets in days. Leave null to keep existing value.",
        default=None,
    )
    default_weight: Decimal | None = gql_field(
        description="Default weight for entities. Leave null to keep existing value.", default=None
    )
    resource_weights: list[ResourceWeightEntryInputGQL] | None = gql_field(
        description="Resource weights for fair share calculation. Each entry specifies a resource type and its weight multiplier. Only provided resource types are updated (partial update). Set weight to null to remove that resource type (revert to default). Leave the entire list null to keep all existing values.",
        default=None,
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description="Payload for resource group fair share spec update mutation.",
    ),
    model=UpdateResourceGroupFairShareSpecPayloadNode,
    name="UpdateResourceGroupFairShareSpecPayload",
)
class UpdateResourceGroupFairShareSpecPayload(
    PydanticOutputMixin[UpdateResourceGroupFairShareSpecPayloadNode]
):
    """Payload for fair share spec update mutation."""

    resource_group: ResourceGroupGQL = gql_field(
        description="The updated resource group with new fair share configuration."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Resource group configuration update input. All fields are optional - only provided fields will be updated. Supports all ScalingGroupUpdaterSpec fields (except fair_share, use separate mutation).",
        added_version="26.2.0",
    ),
    name="UpdateResourceGroupInput",
)
class UpdateResourceGroupInput(PydanticInputMixin[UpdateResourceGroupConfigInputDTO]):
    """Input for updating resource group configuration. All fields optional for partial update."""

    resource_group_name: str = gql_field(description="Name of the resource group to update.")

    # Status fields (ScalingGroupStatusUpdaterSpec)
    is_active: bool | None = gql_field(
        description="Whether the resource group is active. Leave null to keep existing value.",
        default=None,
    )
    is_public: bool | None = gql_field(
        description="Whether the resource group is public. Leave null to keep existing value.",
        default=None,
    )

    # Metadata fields (ScalingGroupMetadataUpdaterSpec)
    description: str | None = gql_field(
        description="Human-readable description. Leave null to keep existing value.", default=None
    )

    # Network config fields (ScalingGroupNetworkConfigUpdaterSpec)
    app_proxy_addr: str | None = gql_field(
        description="App proxy address. Leave null to keep existing value.", default=None
    )
    appproxy_api_token: str | None = gql_field(
        description="App proxy API token. Leave null to keep existing value.", default=None
    )
    use_host_network: bool | None = gql_field(
        description="Whether to use host network mode. Leave null to keep existing value.",
        default=None,
    )

    # Scheduler config fields (ScalingGroupSchedulerConfigUpdaterSpec)
    scheduler_type: SchedulerTypeGQL | None = gql_field(
        description="Scheduler type (FIFO, LIFO, DRF, FAIR_SHARE). Leave null to keep existing value.",
        default=None,
    )
    preemption: PreemptionConfigInput | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.3.0",
            description="Preemption configuration. When provided, replaces the entire preemption config. Leave null to keep existing value.",
        ),
        default=None,
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0", description="Payload for resource group update mutation."
    ),
    model=UpdateResourceGroupConfigPayloadNode,
    name="UpdateResourceGroupPayload",
)
class UpdateResourceGroupPayload(PydanticOutputMixin[UpdateResourceGroupConfigPayloadNode]):
    """Payload for resource group update mutation."""

    resource_group: ResourceGroupGQL = gql_field(
        description="The updated resource group with new configuration."
    )
