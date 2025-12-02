from __future__ import annotations

from typing import Optional

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.agent.types import (
    AgentFilterGQL,
    AgentOrderByGQL,
    AgentResourceGQL,
    AgentStatsGQL,
    AgentV2Connection,
    AgentV2Edge,
    AgentV2GQL,
)
from ai.backend.manager.api.gql.base import to_global_id
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.services.agent.actions.get_total_resources import GetTotalResourcesAction
from ai.backend.manager.services.agent.actions.search_agents import SearchAgentsAction


@strawberry.field(description="Added in 25.15.0")
async def agent_stats(info: Info[StrawberryGQLContext]) -> AgentStatsGQL:
    result = await info.context.processors.agent.get_total_resources.wait_for_complete(
        GetTotalResourcesAction()
    )

    return AgentStatsGQL(
        total_resource=AgentResourceGQL(
            free=result.total_resources.total_free_slots.to_json(),
            used=result.total_resources.total_used_slots.to_json(),
            capacity=result.total_resources.total_capacity_slots.to_json(),
        )
    )


@strawberry.field(description="Added in 25.18.0")
async def agent_v2(
    info: Info[StrawberryGQLContext],
    filter: Optional[AgentFilterGQL] = None,
    order_by: Optional[list[AgentOrderByGQL]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> AgentV2Connection:
    processors = info.context.processors

    querier = info.context.gql_adapters.agent.build_querier(
        filter=filter,
        order_by=order_by,
        first=first,
        after=after,
        last=last,
        before=before,
        limit=limit,
        offset=offset,
    )
    action_result = await processors.agent.search_agents.wait_for_complete(
        SearchAgentsAction(querier=querier)
    )
    permissions = action_result.permissions
    nodes = [AgentV2GQL.from_action_result(data, permissions) for data in action_result.agents]

    edges = [AgentV2Edge(node=node, cursor=to_global_id(AgentV2GQL, node.id)) for node in nodes]

    return AgentV2Connection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )
