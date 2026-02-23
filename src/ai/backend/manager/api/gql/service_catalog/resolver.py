"""GraphQL query resolvers for service catalog."""

from __future__ import annotations

from functools import lru_cache

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only
from ai.backend.manager.models.service_catalog.row import ServiceCatalogRow
from ai.backend.manager.services.service_catalog.actions.search import SearchServiceCatalogsAction

from .types import ServiceCatalogFilterGQL, ServiceCatalogGQL, ServiceCatalogOrderByGQL

__all__ = ("admin_service_catalogs",)


@lru_cache(maxsize=1)
def _get_service_catalog_pagination_spec() -> PaginationSpec:
    """Get pagination spec for ServiceCatalog queries."""
    return PaginationSpec(
        forward_order=ServiceCatalogRow.service_group.asc(),
        backward_order=ServiceCatalogRow.service_group.desc(),
        forward_condition_factory=lambda cursor_value: lambda: ServiceCatalogRow.id > cursor_value,
        backward_condition_factory=lambda cursor_value: lambda: ServiceCatalogRow.id < cursor_value,
        tiebreaker_order=ServiceCatalogRow.id.asc(),
    )


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

    querier = ctx.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        _get_service_catalog_pagination_spec(),
        filter=filter,
        order_by=order_by,
    )

    action = SearchServiceCatalogsAction(querier=querier)
    result = await ctx.processors.service_catalog.search_service_catalogs.wait_for_complete(action)
    return [ServiceCatalogGQL.from_data(catalog) for catalog in result.data]
