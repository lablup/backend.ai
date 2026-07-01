"""Prometheus query preset category GQL query resolvers."""

from __future__ import annotations

from uuid import UUID

from strawberry import ID, Info

from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.request import (
    SearchCategoriesInput,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_root_field,
)
from ai.backend.manager.api.gql.prometheus_query_preset.types.category import (
    CategoryFilterGQL,
    CategoryGQL,
    CategoryOrderByGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext


@gql_root_field(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Get a single query preset category by ID. Available to any authenticated user.",
    )
)  # type: ignore[misc]
async def prometheus_query_preset_category(
    info: Info[StrawberryGQLContext],
    id: ID,
) -> CategoryGQL | None:
    payload = await info.context.adapters.prometheus_query_preset_category.get(UUID(id))
    if payload.item is None:
        return None
    return CategoryGQL.from_pydantic(payload.item)


@gql_root_field(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="List query preset categories with filtering and pagination. Available to any authenticated user.",
    )
)  # type: ignore[misc]
async def prometheus_query_preset_categories(
    info: Info[StrawberryGQLContext],
    filter: CategoryFilterGQL | None = None,
    order_by: list[CategoryOrderByGQL] | None = None,
    first: int | None = None,
    after: str | None = None,
    last: int | None = None,
    before: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> list[CategoryGQL] | None:
    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_order = [o.to_pydantic() for o in order_by] if order_by else None

    payload = await info.context.adapters.prometheus_query_preset_category.search(
        SearchCategoriesInput(
            filter=pydantic_filter,
            order=pydantic_order,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )

    return [CategoryGQL.from_pydantic(node) for node in payload.items]
