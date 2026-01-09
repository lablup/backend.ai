"""Route fetcher functions."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.adapter import PaginationOptions
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.deployment.types.route import (
    Route,
    RouteConnection,
    RouteEdge,
    RouteFilter,
    RouteOrderBy,
    get_route_pagination_spec,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.repositories.base import QueryCondition
from ai.backend.manager.services.deployment.actions.route import (
    SearchRoutesAction,
)


async def fetch_routes(
    info: Info[StrawberryGQLContext],
    filter: Optional[RouteFilter] = None,
    order_by: Optional[list[RouteOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    base_conditions: Optional[list[QueryCondition]] = None,
) -> RouteConnection:
    """Fetch routes with optional filtering, ordering, and pagination.

    Args:
        info: GraphQL context info
        filter: Optional filter criteria
        order_by: Optional ordering specification
        before/after/first/last: Cursor-based pagination parameters
        limit/offset: Offset-based pagination parameters
        base_conditions: Conditions to prepend (e.g., endpoint_id filter from parent type)
    """
    processor = info.context.processors.deployment

    # Build querier using adapter with filter and order_by
    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        get_route_pagination_spec(),
        filter=filter,
        order_by=order_by,
        base_conditions=base_conditions,
    )

    action_result = await processor.search_routes.wait_for_complete(
        SearchRoutesAction(querier=querier)
    )

    nodes = [Route.from_dataclass(data) for data in action_result.routes]
    edges = [RouteEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return RouteConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )


async def fetch_route(
    info: Info[StrawberryGQLContext],
    route_id: UUID,
) -> Optional[Route]:
    """Fetch a specific route by ID."""
    route_info = await info.context.data_loaders.route_loader.load(route_id)
    if route_info is None:
        return None
    return Route.from_dataclass(route_info)
