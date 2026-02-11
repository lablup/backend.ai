from __future__ import annotations

from functools import lru_cache

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.agent.types import (
    AgentV2FilterGQL,
    AgentV2OrderByGQL,
    AgentV2Connection,
    AgentV2Edge,
    AgentV2GQL,
)
from ai.backend.manager.api.gql.base import to_global_id
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.repositories.agent.options import AgentConditions
from ai.backend.manager.services.agent.actions.search_agents import SearchAgentsAction


@lru_cache(maxsize=1)
def _get_agent_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=AgentRow.id.asc(),
        backward_order=AgentRow.id.desc(),
        forward_condition_factory=AgentConditions.by_cursor_forward,
        backward_condition_factory=AgentConditions.by_cursor_backward,
        tiebreaker_order=AgentRow.id.asc(),
    )


async def fetch_agents(
    info: Info[StrawberryGQLContext],
    filter: AgentV2FilterGQL | None = None,
    order_by: list[AgentV2OrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> AgentV2Connection:
    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        pagination_spec=_get_agent_pagination_spec(),
        filter=filter,
        order_by=order_by,
    )

    action_result = await info.context.processors.agent.search_agents.wait_for_complete(
        SearchAgentsAction(querier=querier)
    )
    nodes = [AgentV2GQL.from_agent_detail_data(detail) for detail in action_result.agents]
    edges = [AgentV2Edge(node=node, cursor=to_global_id(AgentV2GQL, node.id)) for node in nodes]

    return AgentV2Connection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )
