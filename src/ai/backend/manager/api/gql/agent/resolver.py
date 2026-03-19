from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.common.dto.manager.v2.agent.request import AdminSearchAgentsInput
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


@strawberry.field(description="Added in 25.15.0")  # type: ignore[misc]
async def agent_stats(info: Info[StrawberryGQLContext]) -> AgentStatsGQL | None:
    result = await info.context.processors.agent.get_total_resources.wait_for_complete(
        GetTotalResourcesAction()
    )

    resource = AgentResourceGQL(
        free=result.total_resources.total_free_slots.to_json(),
        used=result.total_resources.total_used_slots.to_json(),
        capacity=result.total_resources.total_capacity_slots.to_json(),
    )
    return AgentStatsGQL(total_resource=resource)


@strawberry.field(description="Added in 26.1.0")  # type: ignore[misc]
async def agents_v2(
    info: Info[StrawberryGQLContext],
    filter: AgentFilterGQL | None = None,
    order_by: list[AgentOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> AgentV2Connection | None:
    result = await info.context.adapters.agent.admin_search(
        AdminSearchAgentsInput(
            filter=filter.to_pydantic() if filter else None,
            order=[o.to_pydantic() for o in order_by] if order_by else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )
    nodes = [AgentV2GQL.from_pydantic(item) for item in result.items]
    edges = [AgentV2Edge(node=node, cursor=to_global_id(AgentV2GQL, node.id)) for node in nodes]
    return AgentV2Connection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
    )
