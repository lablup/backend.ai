"""GraphQL resolvers for agent queries."""

from __future__ import annotations

from typing import TYPE_CHECKING

import strawberry
from strawberry import ID, Info

from ai.backend.common.types import AgentId

from .types import AgentV2GQL

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.types import StrawberryGQLContext


@strawberry.field(description="Added in 26.1.0. Get an agent by ID.")
async def agent_v2(
    info: Info[StrawberryGQLContext],
    id: ID,
) -> AgentV2GQL | None:
    """Fetch an agent by its ID.

    Args:
        info: GraphQL context info
        id: The ID of the agent to fetch

    Returns:
        AgentV2GQL if found, None otherwise
    """
    # Convert ID to AgentId
    agent_id = AgentId(str(id))

    # For now, just return the AgentV2GQL with the ID
    # The kernels field will be resolved dynamically when queried
    return AgentV2GQL.from_agent_id(agent_id)
