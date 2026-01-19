"""GraphQL query resolvers for scaling group system."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge

from ai.backend.common.contexts.user import current_user
from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.agent.types import AgentResourceGQL, AgentStatsGQL
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.repositories.scaling_group.options import (
    ScalingGroupConditions,
    ScalingGroupOrders,
)
from ai.backend.manager.services.agent.actions.get_scaling_group_resources import (
    GetScalingGroupResourcesAction,
)
from ai.backend.manager.services.scaling_group.actions.list_scaling_groups import (
    SearchScalingGroupsAction,
)

from .types import (
    ScalingGroupFilterGQL,
    ScalingGroupOrderByGQL,
    ScalingGroupV2GQL,
)

# Pagination specs


@lru_cache(maxsize=1)
def _get_scaling_group_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=ScalingGroupOrders.created_at(ascending=False),
        backward_order=ScalingGroupOrders.created_at(ascending=True),
        forward_condition_factory=ScalingGroupConditions.by_cursor_forward,
        backward_condition_factory=ScalingGroupConditions.by_cursor_backward,
    )


# Connection types

ScalingGroupV2Edge = Edge[ScalingGroupV2GQL]


@strawberry.type(description="Added in 25.18.0. Scaling group connection")
class ScalingGroupV2Connection(Connection[ScalingGroupV2GQL]):
    count: int

    def __init__(self, *args, count: int, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# Query fields


@strawberry.field(description="Added in 25.18.0. List scaling groups for a specific project")
async def scaling_groups_v2(
    info: Info[StrawberryGQLContext],
    project: ID,
    filter: Optional[ScalingGroupFilterGQL] = None,
    order_by: Optional[list[ScalingGroupOrderByGQL]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> ScalingGroupV2Connection:
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
        _get_scaling_group_pagination_spec(),
        filter=filter,
        order_by=order_by,
    )

    # Apply project filtering as a required condition
    project_condition = ScalingGroupConditions.by_project(project)
    querier.conditions.append(project_condition)

    action_result = await processors.scaling_group.search_scaling_groups.wait_for_complete(
        SearchScalingGroupsAction(querier=querier)
    )

    nodes = [ScalingGroupV2GQL.from_dataclass(data) for data in action_result.scaling_groups]

    edges = [ScalingGroupV2Edge(node=node, cursor=encode_cursor(node.id)) for node in nodes]

    return ScalingGroupV2Connection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )


@strawberry.field(description="Added in 25.18.0. List all scaling groups")
async def all_scaling_groups_v2(
    info: Info[StrawberryGQLContext],
    filter: Optional[ScalingGroupFilterGQL] = None,
    order_by: Optional[list[ScalingGroupOrderByGQL]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> ScalingGroupV2Connection:
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
        _get_scaling_group_pagination_spec(),
        filter=filter,
        order_by=order_by,
    )

    action_result = await processors.scaling_group.search_scaling_groups.wait_for_complete(
        SearchScalingGroupsAction(querier=querier)
    )

    nodes = [ScalingGroupV2GQL.from_dataclass(data) for data in action_result.scaling_groups]

    edges = [ScalingGroupV2Edge(node=node, cursor=encode_cursor(node.id)) for node in nodes]

    return ScalingGroupV2Connection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )


@strawberry.field(
    description=dedent_strip("""
    Added in 26.1.0. Get aggregated resource stats for a scaling group.
    Returns total capacity, used, and free resource slots for all agents in the scaling group.
    If hide_agents config is enabled and the user is not superadmin, returns empty stats.
""")
)
async def scaling_group_resources(
    info: Info[StrawberryGQLContext],
    scaling_group: str,
    project: ID,
) -> AgentStatsGQL:
    me = current_user()
    if me is None:
        raise InsufficientPrivilege("Authentication required")

    result = await info.context.processors.agent.get_scaling_group_resources.wait_for_complete(
        GetScalingGroupResourcesAction(
            user_data=me,
            scaling_group_name=scaling_group,
            project_id=UUID(str(project)),
            domain_name=me.domain_name,
        )
    )

    return AgentStatsGQL(
        total_resource=AgentResourceGQL(
            free=result.total_resources.total_free_slots.to_json(),
            used=result.total_resources.total_used_slots.to_json(),
            capacity=result.total_resources.total_capacity_slots.to_json(),
        )
    )
