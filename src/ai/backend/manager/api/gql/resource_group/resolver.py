"""GraphQL query resolvers for resource group system."""

from __future__ import annotations

from functools import lru_cache

import strawberry
from strawberry import Info
from strawberry.relay import Connection, Edge

from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import StringMatchSpec, encode_cursor
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.repositories.base import BatchQuerier, NoPagination, Updater
from ai.backend.manager.repositories.scaling_group.options import (
    ScalingGroupConditions,
    ScalingGroupOrders,
)
from ai.backend.manager.repositories.scaling_group.updaters import (
    ResourceGroupFairShareUpdaterSpec,
    ScalingGroupUpdaterSpec,
)
from ai.backend.manager.services.scaling_group.actions.list_scaling_groups import (
    SearchScalingGroupsAction,
)
from ai.backend.manager.services.scaling_group.actions.modify import (
    ModifyScalingGroupAction,
)
from ai.backend.manager.types import TriState

from .types import (
    ResourceGroupFilterGQL,
    ResourceGroupGQL,
    ResourceGroupOrderByGQL,
    UpdateResourceGroupFairShareSpecInput,
    UpdateResourceGroupFairShareSpecPayload,
)

# Pagination specs


@lru_cache(maxsize=1)
def _get_resource_group_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=ScalingGroupOrders.created_at(ascending=False),
        backward_order=ScalingGroupOrders.created_at(ascending=True),
        forward_condition_factory=ScalingGroupConditions.by_cursor_forward,
        backward_condition_factory=ScalingGroupConditions.by_cursor_backward,
    )


# Connection types

ResourceGroupEdge = Edge[ResourceGroupGQL]


@strawberry.type(description="Added in 26.1.0. Resource group connection")
class ResourceGroupConnection(Connection[ResourceGroupGQL]):
    count: int

    def __init__(self, *args, count: int, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# Query fields


@strawberry.field(description="Added in 26.1.0. List resource groups")
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
) -> ResourceGroupConnection:
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


@strawberry.mutation(
    description=(
        "Added in 26.1.0. Update fair share configuration for a resource group (superadmin only). "
        "Only provided fields are updated; others retain their existing values."
    )
)
async def update_resource_group_fair_share_spec(
    info: Info[StrawberryGQLContext],
    input: UpdateResourceGroupFairShareSpecInput,
) -> UpdateResourceGroupFairShareSpecPayload:
    """Update fair share spec with partial update (Read-Modify-Write pattern)."""
    processors = info.context.processors

    # 1. Read: Get existing scaling group
    name_spec = StringMatchSpec(
        value=input.resource_group,
        case_insensitive=False,
        negated=False,
    )
    querier = BatchQuerier(
        pagination=NoPagination(),
        conditions=[ScalingGroupConditions.by_name_equals(name_spec)],
    )
    search_result = await processors.scaling_group.search_scaling_groups.wait_for_complete(
        SearchScalingGroupsAction(querier=querier)
    )

    if not search_result.scaling_groups:
        raise ValueError(f"Resource group '{input.resource_group}' not found")

    existing_data = search_result.scaling_groups[0]

    # 2. Modify: Merge partial input with existing fair_share_spec
    merged_spec = input.merge_with(existing_data.fair_share_spec)

    # 3. Write: Update using the updater
    fair_share_updater = ResourceGroupFairShareUpdaterSpec(
        fair_share_spec=TriState.update(merged_spec),
    )
    updater = Updater[ScalingGroupRow](
        pk_value=input.resource_group,
        spec=ScalingGroupUpdaterSpec(fair_share=fair_share_updater),
    )

    result = await processors.scaling_group.modify_scaling_group.wait_for_complete(
        ModifyScalingGroupAction(updater=updater)
    )

    return UpdateResourceGroupFairShareSpecPayload(
        resource_group=ResourceGroupGQL.from_dataclass(result.scaling_group),
    )
