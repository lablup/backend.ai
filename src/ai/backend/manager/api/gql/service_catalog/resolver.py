"""GraphQL query resolvers for service catalog."""

from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only
from ai.backend.manager.services.service_catalog.actions.search import SearchServiceCatalogsAction

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
    action = SearchServiceCatalogsAction(
        service_group=filter.service_group if filter is not None else None,
        status=filter.status.value if filter is not None and filter.status is not None else None,
        first=first,
        offset=offset,
    )
    result = await ctx.processors.service_catalog.search_service_catalogs.wait_for_complete(action)
    return [ServiceCatalogGQL.from_row(row) for row in result.catalogs]
