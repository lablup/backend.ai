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
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_root_field,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext


@gql_root_field(
    BackendAIGQLMeta(added_version="25.15.0", description="Get aggregate agent resource statistics")
)  # type: ignore[misc]
async def agent_stats(info: Info[StrawberryGQLContext]) -> AgentStatsGQL | None:
    total = await info.context.adapters.agent.get_total_resources()
    resource = AgentResourceGQL(
        free=total.total_free_slots.to_json(),
        used=total.total_used_slots.to_json(),
        capacity=total.total_capacity_slots.to_json(),
    )
    return AgentStatsGQL(total_resource=resource)


@gql_root_field(
    BackendAIGQLMeta(
        added_version="26.1.0", description="List agents with filtering and pagination"
    )
)  # type: ignore[misc]
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
