"""GraphQL query resolvers for scaling group system."""

from __future__ import annotations

from typing import Optional

import strawberry
from strawberry import Info
from strawberry.relay import Connection, Edge

from ai.backend.manager.api.gql.base import to_global_id
from ai.backend.manager.services.scaling_group.actions.list_scaling_groups import (
    SearchScalingGroupsAction,
)

from ..types import StrawberryGQLContext
from .types import (
    GQLScalingGroupFilter,
    GQLScalingGroupOrderBy,
    GQLScalingGroupV2,
)

# Connection types

ScalingGroupEdge = Edge[GQLScalingGroupV2]


@strawberry.type(description="Added in 25.18.0. Scaling group connection")
class ScalingGroupV2Connection(Connection[GQLScalingGroupV2]):
    count: int

    def __init__(self, *args, count: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.count = count


# Query fields


@strawberry.field(description="Added in 25.18.0. List scaling groups")
async def scaling_groups_v2(
    info: Info[StrawberryGQLContext],
    filter: Optional[GQLScalingGroupFilter] = None,
    order_by: Optional[list[GQLScalingGroupOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> ScalingGroupV2Connection:
    processors = info.context.processors

    # Build querier from filter, order_by, and pagination using adapter
    querier = info.context.gql_adapters.scaling_group.build_querier(
        filter=filter,
        order_by=order_by,
        first=first,
        after=after,
        last=last,
        before=before,
        limit=limit,
        offset=offset,
    )

    action_result = await processors.scaling_group.search_scaling_groups.wait_for_complete(
        SearchScalingGroupsAction(querier=querier)
    )

    nodes = [GQLScalingGroupV2.from_dataclass(data) for data in action_result.scaling_groups]

    edges = [
        ScalingGroupEdge(node=node, cursor=to_global_id(GQLScalingGroupV2, node.id))
        for node in nodes
    ]

    # TODO: Get correct has_next_page and has_previous_page values
    return ScalingGroupV2Connection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )
