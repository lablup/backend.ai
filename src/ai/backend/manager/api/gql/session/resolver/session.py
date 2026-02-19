from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry import Info

from ai.backend.common.types import SessionId
from ai.backend.manager.api.gql.session.fetcher import fetch_session, fetch_sessions
from ai.backend.manager.api.gql.session.types import (
    SessionV2ConnectionGQL,
    SessionV2FilterGQL,
    SessionV2GQL,
    SessionV2OrderByGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@strawberry.field(description="Added in 26.2.0. Query a single session by ID.")  # type: ignore[misc]
async def session_v2(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> SessionV2GQL | None:
    return await fetch_session(info, SessionId(id))


@strawberry.field(
    description="Added in 26.2.0. Query sessions with pagination and filtering. (admin only)"
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
    return await fetch_sessions(
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
