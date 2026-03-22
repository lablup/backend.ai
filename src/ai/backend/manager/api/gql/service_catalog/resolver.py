"""GraphQL query resolvers for service catalog."""

from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.common.dto.manager.v2.service_catalog.request import (
    AdminSearchServiceCatalogsInput,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only

from .types import ServiceCatalogFilterGQL, ServiceCatalogGQL, ServiceCatalogOrderByGQL

__all__ = ("admin_service_catalogs",)


@strawberry.field(  # type: ignore[misc]
    description="Added in 26.3.0. Query service catalog entries. Admin only.",
)
async def admin_service_catalogs(
    info: Info[StrawberryGQLContext],
    filter: ServiceCatalogFilterGQL | None = None,
    order_by: list[ServiceCatalogOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> list[ServiceCatalogGQL]:
    check_admin_only()
    ctx = info.context

    search_input = AdminSearchServiceCatalogsInput(
        filter=filter.to_pydantic() if filter is not None else None,
        order=[o.to_pydantic() for o in order_by] if order_by is not None else None,
        first=first,
        after=after,
        last=last,
        before=before,
        limit=limit,
        offset=offset,
    )

    payload = await ctx.adapters.service_catalog.admin_search(search_input)
    return [ServiceCatalogGQL.from_pydantic(item) for item in payload.items]
