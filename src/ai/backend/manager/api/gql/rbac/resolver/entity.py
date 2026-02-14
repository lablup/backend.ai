"""GraphQL resolver for RBAC entity search."""

from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.rbac.fetcher.entity import fetch_entities
from ai.backend.manager.api.gql.rbac.types import EntityConnection, EntityTypeGQL
from ai.backend.manager.api.gql.types import StrawberryGQLContext


@strawberry.field(
    description="Added in 26.3.0. Search entities by type (admin only). Only entity_type selection and pagination are supported. Use each entity's dedicated query for detailed options."
)  # type: ignore[misc]
async def admin_entities(
    info: Info[StrawberryGQLContext],
    entity_type: EntityTypeGQL,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> EntityConnection | None:
    """Search entities by type with pagination only.

    Per-entity filtering and ordering are not provided because EntityNode
    is a union of 15+ types, making a common filter schema impractical.
    Use dedicated root queries (e.g., admin_users, admin_projects) for
    detailed options including filtering and ordering.

    Returns None for entity types without a dedicated fetcher.
    """
    return await fetch_entities(
        info,
        entity_type=entity_type,
        before=before,
        after=after,
        first=first,
        last=last,
        limit=limit,
        offset=offset,
    )
