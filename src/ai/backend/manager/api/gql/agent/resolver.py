from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.agent.fetcher import fetch_agents
from ai.backend.manager.api.gql.agent.types import (
    AgentFilterGQL,
    AgentOrderByGQL,
    AgentResourceGQL,
    AgentStatsGQL,
    AgentV2Connection,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.services.agent.actions.get_total_resources import GetTotalResourcesAction


@strawberry.field(description="Added in 25.15.0")  # type: ignore[misc]
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
) -> AgentV2Connection:
    return await fetch_agents(
        info,
        filter=filter,
        order_by=order_by,
        before=before,
        after=after,
        first=first,
        last=last,
        limit=limit,
        offset=offset,
    )
