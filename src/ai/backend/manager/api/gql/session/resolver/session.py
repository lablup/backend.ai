from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.common.dto.manager.v2.session.request import AdminSearchSessionsInput
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_root_field,
)
from ai.backend.manager.api.gql.session.types import (
    SessionV2ConnectionGQL,
    SessionV2EdgeGQL,
    SessionV2FilterGQL,
    SessionV2GQL,
    SessionV2OrderByGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_root_field(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Query sessions with pagination and filtering. (admin only)",
    )
)  # type: ignore[misc]
async def admin_sessions_v2(
    info: Info[StrawberryGQLContext],
    filter: SessionV2FilterGQL | None = None,
    order_by: list[SessionV2OrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> SessionV2ConnectionGQL:
    check_admin_only()
    payload = await info.context.adapters.session.admin_search(
        AdminSearchSessionsInput(
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
    nodes = [SessionV2GQL.from_pydantic(node) for node in payload.items]
    edges = [SessionV2EdgeGQL(node=node, cursor=encode_cursor(node.id)) for node in nodes]
    return SessionV2ConnectionGQL(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )
