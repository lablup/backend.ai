"""GraphQL resolver for RBAC entity search."""

from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.common.dto.manager.v2.rbac.request import AdminSearchEntitiesGQLInput
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.rbac.types import (
    EntityConnection,
    EntityFilter,
    EntityOrderBy,
)
from ai.backend.manager.api.gql.rbac.types.entity import EntityEdge, EntityRefGQL
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


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
    check_admin_only()
    result = await info.context.adapters.rbac.admin_search_entities_gql(
        AdminSearchEntitiesGQLInput(
            filter=filter.to_pydantic() if filter is not None else None,
            order=[o.to_pydantic() for o in order_by] if order_by is not None else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )
    edges = [
        EntityEdge(
            node=EntityRefGQL.from_pydantic(item),
            cursor=encode_cursor(str(item.id)),
        )
        for item in result.items
    ]
    return EntityConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
    )
