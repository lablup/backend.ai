from __future__ import annotations

import strawberry
from strawberry import Info
from strawberry.scalars import JSON

from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.services.agent.actions.get_total_resources import GetTotalResourcesAction


@strawberry.field(description="Added in 25.15.0")
async def agent_stats(info: Info[StrawberryGQLContext]) -> AgentStats:
    result = await info.context.processors.agent.get_total_resources.wait_for_complete(
        GetTotalResourcesAction()
    )

    return AgentStats(
        total_resource=AgentResource(
            free=result.total_resources.total_free_slots.to_json(),
            used=result.total_resources.total_used_slots.to_json(),
            capacity=result.total_resources.total_capacity_slots.to_json(),
        )
    )


@strawberry.type(description="Added in 25.15.0")
class AgentResource:
    free: JSON
    used: JSON
    capacity: JSON


@strawberry.type(description="Added in 25.15.0")
class AgentStats:
    total_resource: AgentResource = strawberry.field(description="Added in 25.15.0")
