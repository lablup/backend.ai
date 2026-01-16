from __future__ import annotations

from functools import lru_cache
from uuid import UUID

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import to_global_id
from ai.backend.manager.api.gql.session.types import (
    SessionConnectionV2GQL,
    SessionEdgeGQL,
    SessionFilterGQL,
    SessionOrderByGQL,
    SessionV2GQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.repositories.scheduler.options import SessionConditions
from ai.backend.manager.services.session.actions.search_session import SearchSessionsAction


@lru_cache(maxsize=1)
def _get_session_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=SessionRow.created_at.desc(),
        backward_order=SessionRow.created_at.asc(),
        forward_condition_factory=SessionConditions.by_cursor_forward,
        backward_condition_factory=SessionConditions.by_cursor_backward,
    )


async def fetch_sessions(
    info: Info[StrawberryGQLContext],
    filter: SessionFilterGQL | None = None,
    order_by: list[SessionOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> SessionConnectionV2GQL:
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
    )

    action_result = await info.context.processors.session.search_sessions.wait_for_complete(
        SearchSessionsAction(querier=querier)
    )
    nodes = [SessionV2GQL.from_session_info(session_info) for session_info in action_result.data]
    edges = [
        SessionEdgeGQL(node=node, cursor=to_global_id(SessionV2GQL, node.id)) for node in nodes
    ]

    return SessionConnectionV2GQL(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )


async def fetch_session(
    info: Info[StrawberryGQLContext],
    session_id: UUID,
) -> SessionV2GQL | None:
    """Fetch a single session by ID."""
    filter = SessionFilterGQL(id=session_id)
    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(limit=1),
        pagination_spec=_get_session_pagination_spec(),
        filter=filter,
        order_by=None,
    )

    action_result = await info.context.processors.session.search_sessions.wait_for_complete(
        SearchSessionsAction(querier=querier)
    )

    if not action_result.data:
        return None

    return SessionV2GQL.from_session_info(action_result.data[0])
