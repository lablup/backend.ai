from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry import ID, Info

from ai.backend.manager.api.gql.session.fetcher import fetch_session, fetch_sessions
from ai.backend.manager.api.gql.session.types import (
    SessionConnectionV2GQL,
    SessionFilterGQL,
    SessionOrderByGQL,
    SessionV2GQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext


@strawberry.field(description="Added in 26.1.0. Query a single session by ID.")
async def session_v2(
    info: Info[StrawberryGQLContext],
    id: ID,
) -> SessionV2GQL | None:
    return await fetch_session(info, UUID(id))


@strawberry.field(description="Added in 26.1.0. Query sessions with pagination and filtering.")
async def sessions_v2(
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
