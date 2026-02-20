"""GraphQL resolver for RBAC entity search."""

from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.rbac.fetcher.entity import fetch_entities
from ai.backend.manager.api.gql.rbac.types import (
    EntityConnection,
    EntityFilter,
    EntityOrderBy,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext


@strawberry.field(
    description="Added in 26.3.0. Search entity associations (admin only). Optionally filter by entity_type and entity_id."
)  # type: ignore[misc]
async def admin_entities(
    info: Info[StrawberryGQLContext],
    filter: EntityFilter | None = None,
    order_by: list[EntityOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> EntityConnection:
    """Search entity associations with filtering, ordering, and pagination."""
    return await fetch_entities(
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
