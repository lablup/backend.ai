from __future__ import annotations

import strawberry
from strawberry import Info
from strawberry.scalars import JSON

from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.services.agent.actions.get_total_resources import GetTotalResourcesAction


@strawberry.field(description="Added in 25.15.0")
async def agent_stats() -> AgentStats:
    return AgentStats()


@strawberry.type(description="Added in 25.15.0")
class AgentStats:
    @strawberry.field(description="Added in 25.15.0")
    async def total_used_slots(self, info: Info["StrawberryGQLContext"]) -> JSON:
        result = await info.context.processors.agent.get_total_resources.wait_for_complete(
            GetTotalResourcesAction()
        )
        return result.total_resources.total_used_slots
