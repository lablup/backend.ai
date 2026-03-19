"""GraphQL query resolvers for resource group system."""

from __future__ import annotations

from typing import Any

import strawberry
from strawberry import Info
from strawberry.relay import Connection, Edge, PageInfo

from ai.backend.common.dto.manager.v2.resource_group.request import AdminSearchResourceGroupsInput
from ai.backend.common.types import PreemptionMode, PreemptionOrder
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only
from ai.backend.manager.data.scaling_group.types import (
    PreemptionConfig as DataPreemptionConfig,
)
from ai.backend.manager.data.scaling_group.types import (
    SchedulerType,
)
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.scaling_group.updaters import (
    ScalingGroupMetadataUpdaterSpec,
    ScalingGroupNetworkConfigUpdaterSpec,
    ScalingGroupSchedulerConfigUpdaterSpec,
    ScalingGroupStatusUpdaterSpec,
    ScalingGroupUpdaterSpec,
)
from ai.backend.manager.services.scaling_group.actions.modify import (
    ModifyScalingGroupAction,
)
from ai.backend.manager.services.scaling_group.actions.update_fair_share_spec import (
    ResourceWeightInput,
    UpdateFairShareSpecAction,
)
from ai.backend.manager.types import OptionalState, TriState

from .types import (
    ResourceGroupFilterGQL,
    ResourceGroupGQL,
    ResourceGroupOrderByGQL,
    UpdateResourceGroupFairShareSpecInput,
    UpdateResourceGroupFairShareSpecPayload,
    UpdateResourceGroupInput,
    UpdateResourceGroupPayload,
)

# Connection types

ResourceGroupEdge = Edge[ResourceGroupGQL]


@strawberry.type(description="Added in 26.2.0. Resource group connection")
class ResourceGroupConnection(Connection[ResourceGroupGQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# Query fields


@strawberry.field(  # type: ignore[misc]
    description="Added in 26.2.0. List resource groups (admin only)",
)
async def admin_resource_groups(
    info: Info[StrawberryGQLContext],
    filter: ResourceGroupFilterGQL | None = None,
    order_by: list[ResourceGroupOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ResourceGroupConnection | None:
    check_admin_only()

    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_order = [o.to_pydantic() for o in order_by] if order_by else None

    payload = await info.context.adapters.resource_group.search(
        AdminSearchResourceGroupsInput(
            filter=pydantic_filter,
            order=pydantic_order,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )

    nodes = [ResourceGroupGQL.from_node(data) for data in payload.items]
    edges = [ResourceGroupEdge(node=node, cursor=encode_cursor(node.id)) for node in nodes]

    return ResourceGroupConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )


@strawberry.field(  # type: ignore[misc]
    description="Added in 26.2.0. List resource groups",
    deprecation_reason=(
        "Use admin_resource_groups instead. This API will be removed after v26.3.0. "
        "See BEP-1041 for migration guide."
    ),
)
async def resource_groups(
    info: Info[StrawberryGQLContext],
    filter: ResourceGroupFilterGQL | None = None,
    order_by: list[ResourceGroupOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ResourceGroupConnection | None:
    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_order = [o.to_pydantic() for o in order_by] if order_by else None

    payload = await info.context.adapters.resource_group.search(
        AdminSearchResourceGroupsInput(
            filter=pydantic_filter,
            order=pydantic_order,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )

    nodes = [ResourceGroupGQL.from_node(data) for data in payload.items]
    edges = [ResourceGroupEdge(node=node, cursor=encode_cursor(node.id)) for node in nodes]

    return ResourceGroupConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )


# Mutation fields


@strawberry.mutation(  # type: ignore[misc]
    description=(
        "Added in 26.2.0. Update fair share configuration for a resource group (admin only). "
        "Only provided fields are updated; others retain their existing values. "
        "Resource weights are validated against capacity - only resource types available in "
        "the scaling group's capacity can be specified."
    )
)
async def admin_update_resource_group_fair_share_spec(
    info: Info[StrawberryGQLContext],
    input: UpdateResourceGroupFairShareSpecInput,
) -> UpdateResourceGroupFairShareSpecPayload:
    """Update fair share spec with partial update and validation."""
    check_admin_only()

    processors = info.context.processors
    dto = input.to_pydantic()

    resource_weights = None
    if dto.resource_weights is not None:
        resource_weights = [
            ResourceWeightInput(
                resource_type=entry.resource_type,
                weight=entry.weight,
            )
            for entry in dto.resource_weights
        ]

    action = UpdateFairShareSpecAction(
        resource_group=dto.resource_group_name,
        half_life_days=dto.half_life_days,
        lookback_days=dto.lookback_days,
        decay_unit_days=dto.decay_unit_days,
        default_weight=dto.default_weight,
        resource_weights=resource_weights,
    )

    result = await processors.scaling_group.update_fair_share_spec.wait_for_complete(action)

    return UpdateResourceGroupFairShareSpecPayload(
        resource_group=ResourceGroupGQL.from_node(result.scaling_group),
    )


@strawberry.mutation(  # type: ignore[misc]
    description=(
        "Added in 26.2.0. Update fair share configuration for a resource group (superadmin only). "
        "Only provided fields are updated; others retain their existing values. "
        "Resource weights are validated against capacity - only resource types available in "
        "the scaling group's capacity can be specified."
    ),
    deprecation_reason=(
        "Use admin_update_resource_group_fair_share_spec instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)
async def update_resource_group_fair_share_spec(
    info: Info[StrawberryGQLContext],
    input: UpdateResourceGroupFairShareSpecInput,
) -> UpdateResourceGroupFairShareSpecPayload:
    """Update fair share spec with partial update and validation."""
    processors = info.context.processors
    dto = input.to_pydantic()

    resource_weights = None
    if dto.resource_weights is not None:
        resource_weights = [
            ResourceWeightInput(
                resource_type=entry.resource_type,
                weight=entry.weight,
            )
            for entry in dto.resource_weights
        ]

    action = UpdateFairShareSpecAction(
        resource_group=dto.resource_group_name,
        half_life_days=dto.half_life_days,
        lookback_days=dto.lookback_days,
        decay_unit_days=dto.decay_unit_days,
        default_weight=dto.default_weight,
        resource_weights=resource_weights,
    )

    result = await processors.scaling_group.update_fair_share_spec.wait_for_complete(action)

    return UpdateResourceGroupFairShareSpecPayload(
        resource_group=ResourceGroupGQL.from_node(result.scaling_group),
    )


@strawberry.mutation(  # type: ignore[misc]
    description=(
        "Added in 26.2.0. Update resource group configuration (admin only). "
        "Only provided fields are updated; others retain their existing values. "
        "Supports all configuration fields except fair_share (use separate mutation)."
    )
)
async def admin_update_resource_group(
    info: Info[StrawberryGQLContext],
    input: UpdateResourceGroupInput,
) -> UpdateResourceGroupPayload:
    """Update resource group configuration with partial update."""
    check_admin_only()

    processors = info.context.processors
    dto = input.to_pydantic()

    status_spec = ScalingGroupStatusUpdaterSpec(
        is_active=(
            OptionalState.update(dto.is_active)
            if dto.is_active is not None
            else OptionalState.nop()
        ),
        is_public=(
            OptionalState.update(dto.is_public)
            if dto.is_public is not None
            else OptionalState.nop()
        ),
    )

    metadata_spec = ScalingGroupMetadataUpdaterSpec(
        description=(
            TriState.update(dto.description) if dto.description is not None else TriState.nop()
        ),
    )

    network_spec = ScalingGroupNetworkConfigUpdaterSpec(
        wsproxy_addr=(
            TriState.update(dto.app_proxy_addr)
            if dto.app_proxy_addr is not None
            else TriState.nop()
        ),
        wsproxy_api_token=(
            TriState.update(dto.appproxy_api_token)
            if dto.appproxy_api_token is not None
            else TriState.nop()
        ),
        use_host_network=(
            OptionalState.update(dto.use_host_network)
            if dto.use_host_network is not None
            else OptionalState.nop()
        ),
    )

    # Convert scheduler_type from DTO str to internal type
    scheduler_value: str | None = None
    if dto.scheduler_type is not None:
        scheduler_value = SchedulerType(dto.scheduler_type).value

    # Handle preemption config update
    preemption_config_state: OptionalState[DataPreemptionConfig] = OptionalState.nop()
    if dto.preemption is not None:
        preemption_config_state = OptionalState.update(
            DataPreemptionConfig(
                preemptible_priority=dto.preemption.preemptible_priority,
                order=PreemptionOrder(dto.preemption.order),
                mode=PreemptionMode(dto.preemption.mode),
            )
        )

    scheduler_spec = ScalingGroupSchedulerConfigUpdaterSpec(
        scheduler=(
            OptionalState.update(scheduler_value)
            if scheduler_value is not None
            else OptionalState.nop()
        ),
        preemption_config=preemption_config_state,
    )

    # Composite spec (excludes fair_share - use separate mutation)
    updater_spec = ScalingGroupUpdaterSpec(
        status=status_spec,
        metadata=metadata_spec,
        network=network_spec,
        scheduler=scheduler_spec,
    )

    updater = Updater(spec=updater_spec, pk_value=dto.resource_group_name)

    action = ModifyScalingGroupAction(updater=updater)

    result = await processors.scaling_group.modify_scaling_group.wait_for_complete(action)

    return UpdateResourceGroupPayload(
        resource_group=ResourceGroupGQL.from_node(result.scaling_group),
    )
