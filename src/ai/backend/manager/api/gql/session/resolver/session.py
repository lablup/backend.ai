from __future__ import annotations

import strawberry
from strawberry import ID, Info

from ai.backend.manager.api.gql.session.types import (
    SessionConnectionV2GQL,
    SessionFilterGQL,
    SessionOrderByGQL,
    SessionV2GQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext


@strawberry.field(description="Added in 26.2.0. Query a single session by ID.")  # type: ignore[misc]
async def session_v2(
    info: Info[StrawberryGQLContext],
    id: ID,
) -> SessionV2GQL | None:
    _ = info, id
    raise NotImplementedError


@strawberry.field(description="Added in 26.2.0. Query sessions with pagination and filtering.")  # type: ignore[misc]
async def admin_sessions_v2(
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
    _ = info, filter, order_by, before, after, first, last, limit, offset
    raise NotImplementedError
