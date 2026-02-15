"""GraphQL query resolvers for service catalog."""

from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only

from .fetcher import fetch_service_catalogs
from .types import ServiceCatalogFilterGQL, ServiceCatalogGQL

__all__ = ("admin_service_catalogs",)


@strawberry.field(  # type: ignore[misc]
    description="Added in 26.3.0. Query service catalog entries. Admin only.",
)
async def admin_service_catalogs(
    info: Info[StrawberryGQLContext],
    filter: ServiceCatalogFilterGQL | None = None,
    first: int | None = None,
    offset: int | None = None,
) -> list[ServiceCatalogGQL]:
    check_admin_only()
    ctx = info.context
    if ctx.db is None:
        return []
    return await fetch_service_catalogs(
        db=ctx.db,
        filter=filter,
        first=first,
        offset=offset,
    )
