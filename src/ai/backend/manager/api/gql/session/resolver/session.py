from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.session.types import (
    SessionV2ConnectionGQL,
    SessionV2FilterGQL,
    SessionV2OrderByGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext


@strawberry.field(description="Added in 26.2.0. Query sessions with pagination and filtering.")  # type: ignore[misc]
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
    _ = info, filter, order_by, before, after, first, last, limit, offset
    raise NotImplementedError
