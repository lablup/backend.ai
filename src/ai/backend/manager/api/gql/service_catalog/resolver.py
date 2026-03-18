"""GraphQL query resolvers for service catalog."""

from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.common.dto.manager.query import StringFilter as PydanticStringFilter
from ai.backend.common.dto.manager.v2.service_catalog.request import (
    AdminSearchServiceCatalogsInput,
    ServiceCatalogFilter,
    ServiceCatalogOrder,
)
from ai.backend.common.dto.manager.v2.service_catalog.types import (
    OrderDirection as DtoOrderDirection,
)
from ai.backend.common.dto.manager.v2.service_catalog.types import (
    ServiceCatalogOrderField,
    ServiceCatalogStatusFilter,
)
from ai.backend.common.types import ServiceCatalogStatus
from ai.backend.manager.api.gql.base import OrderDirection as GqlOrderDirection
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

    # Convert GQL filter to Pydantic DTO
    pydantic_filter: ServiceCatalogFilter | None = None
    if filter is not None:
        pydantic_sg: PydanticStringFilter | None = None
        if filter.service_group is not None:
            sg = filter.service_group
            pydantic_sg = PydanticStringFilter(
                equals=sg.equals,
                contains=sg.contains,
                starts_with=sg.starts_with,
                ends_with=sg.ends_with,
                not_equals=sg.not_equals,
                i_equals=sg.i_equals,
                i_contains=sg.i_contains,
                i_starts_with=sg.i_starts_with,
                i_ends_with=sg.i_ends_with,
                i_not_equals=sg.i_not_equals,
            )
        pydantic_status: ServiceCatalogStatusFilter | None = None
        if filter.status is not None:
            st = filter.status
            pydantic_status = ServiceCatalogStatusFilter(
                equals=ServiceCatalogStatus(st.equals.value) if st.equals is not None else None,
                in_=(
                    [ServiceCatalogStatus(s.value) for s in st.in_] if st.in_ is not None else None
                ),
                not_equals=(
                    ServiceCatalogStatus(st.not_equals.value) if st.not_equals is not None else None
                ),
                not_in=(
                    [ServiceCatalogStatus(s.value) for s in st.not_in]
                    if st.not_in is not None
                    else None
                ),
            )
        pydantic_filter = ServiceCatalogFilter(
            service_group=pydantic_sg,
            status=pydantic_status,
        )

    # Convert GQL orders to Pydantic DTO
    pydantic_orders: list[ServiceCatalogOrder] | None = None
    if order_by is not None:
        pydantic_orders = [
            ServiceCatalogOrder(
                field=ServiceCatalogOrderField[o.field.name],
                direction=(
                    DtoOrderDirection.ASC
                    if o.direction == GqlOrderDirection.ASC
                    else DtoOrderDirection.DESC
                ),
            )
            for o in order_by
        ]

    search_input = AdminSearchServiceCatalogsInput(
        filter=pydantic_filter,
        order=pydantic_orders,
        first=first,
        after=after,
        last=last,
        before=before,
        limit=limit,
        offset=offset,
    )

    payload = await ctx.adapters.service_catalog.admin_search(search_input)
    return [ServiceCatalogGQL.from_pydantic(item) for item in payload.items]
