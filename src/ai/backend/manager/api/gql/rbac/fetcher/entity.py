"""Fetcher for RBAC entity search."""

from __future__ import annotations

from functools import lru_cache

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.rbac.types import (
    EntityConnection,
    EntityFilter,
    EntityOrderBy,
)
from ai.backend.manager.api.gql.rbac.types.entity import EntityEdge, EntityRefGQL
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.repositories.base import QueryCondition
from ai.backend.manager.repositories.permission_controller.options import (
    EntityScopeConditions,
    EntityScopeOrders,
)
from ai.backend.manager.services.permission_contoller.actions.search_element_associations import (
    SearchElementAssociationsAction,
)


@lru_cache(maxsize=1)
def get_entity_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=EntityScopeOrders.id(ascending=False),
        backward_order=EntityScopeOrders.id(ascending=True),
        forward_condition_factory=EntityScopeConditions.by_cursor_forward,
        backward_condition_factory=EntityScopeConditions.by_cursor_backward,
        tiebreaker_order=AssociationScopesEntitiesRow.id.asc(),
    )


async def fetch_entities(
    info: Info[StrawberryGQLContext],
    filter: EntityFilter | None = None,
    order_by: list[EntityOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
    base_conditions: list[QueryCondition] | None = None,
) -> EntityConnection:
    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        get_entity_pagination_spec(),
        filter=filter,
        order_by=order_by,
        base_conditions=base_conditions,
    )

    action_result = await info.context.processors.permission_controller.search_element_associations.wait_for_complete(
        SearchElementAssociationsAction(querier=querier)
    )

    result = action_result.result
    edges = [
        EntityEdge(
            node=EntityRefGQL.from_dataclass(item),
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
