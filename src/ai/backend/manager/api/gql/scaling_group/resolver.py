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
from .types import ScalingGroup, ScalingGroupFilter, ScalingGroupOrderBy

# Connection types

ScalingGroupEdge = Edge[ScalingGroup]


@strawberry.type(description="Scaling group connection")
class ScalingGroupConnection(Connection[ScalingGroup]):
    count: int

    def __init__(self, *args, count: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.count = count


# Query fields


@strawberry.field(description="List scaling groups")
async def scaling_groups(
    info: Info[StrawberryGQLContext],
    filter: Optional[ScalingGroupFilter] = None,
    order_by: Optional[ScalingGroupOrderBy] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> ScalingGroupConnection:
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

    nodes = [ScalingGroup.from_dataclass(data) for data in action_result.scaling_groups]

    edges = [
        ScalingGroupEdge(node=node, cursor=to_global_id(ScalingGroup, node.id)) for node in nodes
    ]

    return ScalingGroupConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )
