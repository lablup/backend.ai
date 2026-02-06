from __future__ import annotations

from uuid import UUID

from strawberry import Info

from ai.backend.manager.api.gql.session.types import (
    SessionConnectionV2GQL,
    SessionFilterGQL,
    SessionOrderByGQL,
    SessionV2GQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext


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
    raise NotImplementedError


async def fetch_session(
    info: Info[StrawberryGQLContext],
    session_id: UUID,
) -> SessionV2GQL | None:
    """Fetch a single session by ID."""
    raise NotImplementedError
