"""Fetcher for RBAC entity search."""

from __future__ import annotations

from strawberry import Info

from ai.backend.manager.api.gql.rbac.types import EntityConnection, EntityTypeGQL
from ai.backend.manager.api.gql.types import StrawberryGQLContext


async def fetch_entities(
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
