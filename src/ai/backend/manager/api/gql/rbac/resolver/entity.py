"""GraphQL resolver for RBAC entity search."""

from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.rbac.types import EntityConnection, EntityTypeGQL
from ai.backend.manager.api.gql.types import StrawberryGQLContext


@strawberry.field(description="Added in 26.3.0. Search entities by type (admin only).")  # type: ignore[misc]
async def admin_entities(
    info: Info[StrawberryGQLContext],
    entity_type: EntityTypeGQL,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> EntityConnection:
    raise NotImplementedError
