"""GraphQL query resolvers for resource group system."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import strawberry
from strawberry import Info
from strawberry.relay import Connection, Edge

from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only
from ai.backend.manager.data.scaling_group.types import SchedulerType
from ai.backend.manager.models.scaling_group.row import ScalingGroupRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.scaling_group.options import (
    ScalingGroupConditions,
    ScalingGroupOrders,
)
from ai.backend.manager.repositories.scaling_group.updaters import (
    ScalingGroupMetadataUpdaterSpec,
    ScalingGroupNetworkConfigUpdaterSpec,
    ScalingGroupSchedulerConfigUpdaterSpec,
    ScalingGroupStatusUpdaterSpec,
    ScalingGroupUpdaterSpec,
)
from ai.backend.manager.services.scaling_group.actions.list_scaling_groups import (
    SearchScalingGroupsAction,
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

# Pagination specs


@lru_cache(maxsize=1)
def _get_resource_group_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=ScalingGroupOrders.created_at(ascending=False),
        backward_order=ScalingGroupOrders.created_at(ascending=True),
        forward_condition_factory=ScalingGroupConditions.by_cursor_forward,
        backward_condition_factory=ScalingGroupConditions.by_cursor_backward,
        tiebreaker_order=ScalingGroupRow.name.asc(),
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

    processors = info.context.processors

    # Build querier from filter, order_by, and pagination using adapter
    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        _get_resource_group_pagination_spec(),
        filter=filter,
        order_by=order_by,
    )

    action_result = await processors.scaling_group.search_scaling_groups.wait_for_complete(
        SearchScalingGroupsAction(querier=querier)
    )

    nodes = [ResourceGroupGQL.from_dataclass(data) for data in action_result.scaling_groups]

    edges = [ResourceGroupEdge(node=node, cursor=encode_cursor(node.id)) for node in nodes]

    return ResourceGroupConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
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
    processors = info.context.processors

    # Build querier from filter, order_by, and pagination using adapter
    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        _get_resource_group_pagination_spec(),
        filter=filter,
        order_by=order_by,
    )

    action_result = await processors.scaling_group.search_scaling_groups.wait_for_complete(
        SearchScalingGroupsAction(querier=querier)
    )

    nodes = [ResourceGroupGQL.from_dataclass(data) for data in action_result.scaling_groups]

    edges = [ResourceGroupEdge(node=node, cursor=encode_cursor(node.id)) for node in nodes]

    return ResourceGroupConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
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

    # Convert GQL input to action
    resource_weights = None
    if input.resource_weights is not None:
        resource_weights = [
            ResourceWeightInput(
                resource_type=entry.resource_type,
                weight=entry.weight,
            )
            for entry in input.resource_weights
        ]

    action = UpdateFairShareSpecAction(
        resource_group=input.resource_group_name,
        half_life_days=input.half_life_days,
        lookback_days=input.lookback_days,
        decay_unit_days=input.decay_unit_days,
        default_weight=input.default_weight,
        resource_weights=resource_weights,
    )

    result = await processors.scaling_group.update_fair_share_spec.wait_for_complete(action)

    return UpdateResourceGroupFairShareSpecPayload(
        resource_group=ResourceGroupGQL.from_dataclass(result.scaling_group),
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

    # Convert GQL input to action
    resource_weights = None
    if input.resource_weights is not None:
        resource_weights = [
            ResourceWeightInput(
                resource_type=entry.resource_type,
                weight=entry.weight,
            )
            for entry in input.resource_weights
        ]

    action = UpdateFairShareSpecAction(
        resource_group=input.resource_group_name,
        half_life_days=input.half_life_days,
        lookback_days=input.lookback_days,
        decay_unit_days=input.decay_unit_days,
        default_weight=input.default_weight,
        resource_weights=resource_weights,
    )

    result = await processors.scaling_group.update_fair_share_spec.wait_for_complete(action)

    return UpdateResourceGroupFairShareSpecPayload(
        resource_group=ResourceGroupGQL.from_dataclass(result.scaling_group),
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

    # Build UpdaterSpec from input
    status_spec = ScalingGroupStatusUpdaterSpec(
        is_active=(
            OptionalState.update(input.is_active)
            if input.is_active is not None
            else OptionalState.nop()
        ),
        is_public=(
            OptionalState.update(input.is_public)
            if input.is_public is not None
            else OptionalState.nop()
        ),
    )

    metadata_spec = ScalingGroupMetadataUpdaterSpec(
        description=(
            TriState.update(input.description) if input.description is not None else TriState.nop()
        ),
    )

    network_spec = ScalingGroupNetworkConfigUpdaterSpec(
        wsproxy_addr=(
            TriState.update(input.app_proxy_addr)
            if input.app_proxy_addr is not None
            else TriState.nop()
        ),
        wsproxy_api_token=(
            TriState.update(input.appproxy_api_token)
            if input.appproxy_api_token is not None
            else TriState.nop()
        ),
        use_host_network=(
            OptionalState.update(input.use_host_network)
            if input.use_host_network is not None
            else OptionalState.nop()
        ),
    )

    # Convert scheduler_type from GQL enum to internal type
    scheduler_value: str | None = None
    if input.scheduler_type is not None:
        scheduler_value = SchedulerType(input.scheduler_type.value).value

    scheduler_spec = ScalingGroupSchedulerConfigUpdaterSpec(
        scheduler=(
            OptionalState.update(scheduler_value)
            if scheduler_value is not None
            else OptionalState.nop()
        ),
    )

    # Composite spec (excludes fair_share - use separate mutation)
    updater_spec = ScalingGroupUpdaterSpec(
        status=status_spec,
        metadata=metadata_spec,
        network=network_spec,
        scheduler=scheduler_spec,
    )

    updater = Updater(spec=updater_spec, pk_value=input.resource_group_name)

    # Use existing ModifyScalingGroupAction
    action = ModifyScalingGroupAction(updater=updater)

    result = await processors.scaling_group.modify_scaling_group.wait_for_complete(action)

    return UpdateResourceGroupPayload(
        resource_group=ResourceGroupGQL.from_dataclass(result.scaling_group),
    )
