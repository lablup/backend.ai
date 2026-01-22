"""GraphQL query resolvers for resource group system."""

from __future__ import annotations

from functools import lru_cache

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge

from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.repositories.scaling_group.options import (
    ScalingGroupConditions,
    ScalingGroupOrders,
)
from ai.backend.manager.services.scaling_group.actions.list_scaling_groups import (
    SearchScalingGroupsAction,
)

from .types import (
    ResourceGroupFilterGQL,
    ResourceGroupGQL,
    ResourceGroupOrderByGQL,
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


@strawberry.field(description="Added in 26.1.0. List resource groups for a specific project")
async def resource_groups(
    info: Info[StrawberryGQLContext],
    project: ID,
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

    # Apply project filtering as a required condition
    project_condition = ScalingGroupConditions.by_project(project)
    querier.conditions.append(project_condition)

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


@strawberry.field(description="Added in 26.1.0. List all resource groups")
async def all_resource_groups(
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
