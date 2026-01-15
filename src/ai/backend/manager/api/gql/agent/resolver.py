"""GraphQL resolvers for agent queries."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import strawberry
from strawberry import Info

from ai.backend.manager.services.agent.actions.get_total_resources import GetTotalResourcesAction

from .fetcher import fetch_agents
from .types import (
    AgentFilterGQL,
    AgentOrderByGQL,
    AgentResourceGQL,
    AgentStatsGQL,
    AgentV2Connection,
)

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.types import StrawberryGQLContext


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


@strawberry.field(description="Added in 26.1.0")
async def agents_v2(
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
