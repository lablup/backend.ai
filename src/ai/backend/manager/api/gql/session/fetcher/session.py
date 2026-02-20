from __future__ import annotations

from functools import lru_cache

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.session.types import (
    SessionV2ConnectionGQL,
    SessionV2EdgeGQL,
    SessionV2FilterGQL,
    SessionV2GQL,
    SessionV2OrderByGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.repositories.base import QueryCondition
from ai.backend.manager.repositories.scheduler.options import SessionConditions, SessionOrders
from ai.backend.manager.services.session.actions.search import SearchSessionsAction


@lru_cache(maxsize=1)
def _get_session_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=SessionOrders.created_at(ascending=False),
        backward_order=SessionOrders.created_at(ascending=True),
        forward_condition_factory=SessionConditions.by_cursor_forward,
        backward_condition_factory=SessionConditions.by_cursor_backward,
        tiebreaker_order=SessionRow.id.asc(),
    )


async def fetch_sessions(
    info: Info[StrawberryGQLContext],
    filter: SessionV2FilterGQL | None = None,
    order_by: list[SessionV2OrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
    base_conditions: list[QueryCondition] | None = None,
) -> SessionV2ConnectionGQL:
    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        pagination_spec=_get_session_pagination_spec(),
        filter=filter,
        order_by=order_by,
        base_conditions=base_conditions,
    )

    action_result = await info.context.processors.session.search_sessions.wait_for_complete(
        SearchSessionsAction(querier=querier)
    )

    nodes = [SessionV2GQL.from_data(session_data) for session_data in action_result.data]
    edges = [SessionV2EdgeGQL(node=node, cursor=encode_cursor(node.id)) for node in nodes]

    return SessionV2ConnectionGQL(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )
