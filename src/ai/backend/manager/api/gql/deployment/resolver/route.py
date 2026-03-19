"""Route resolver functions."""

from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import PageInfo

from ai.backend.common.dto.manager.v2.deployment.request import SearchRoutesInput
from ai.backend.manager.api.gql.base import encode_cursor, resolve_global_id
from ai.backend.manager.api.gql.deployment.types.route import (
    Route,
    RouteConnection,
    RouteEdge,
    RouteFilter,
    RouteOrderBy,
    UpdateRouteTrafficStatusInputGQL,
    UpdateRouteTrafficStatusPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.data.deployment.types import (
    RouteSearchScope,
)
from ai.backend.manager.data.deployment.types import (
    RouteTrafficStatus as RouteTrafficStatusEnum,
)
from ai.backend.manager.services.deployment.actions.route import (
    UpdateRouteTrafficStatusAction,
)

# Query resolvers


@strawberry.field(  # type: ignore[misc]
    description="Added in 25.19.0. List routes for a deployment with optional filters."
)
async def routes(
    info: Info[StrawberryGQLContext],
    deployment_id: ID,
    filter: RouteFilter | None = None,
    order_by: list[RouteOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> RouteConnection | None:
    """List routes for a deployment with optional filters."""
    _, endpoint_id = resolve_global_id(deployment_id)
    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_order = [o.to_pydantic() for o in order_by] if order_by else None
    payload = await info.context.adapters.deployment.search_routes(
        scope=RouteSearchScope(deployment_id=UUID(endpoint_id)),
        input=SearchRoutesInput(
            filter=pydantic_filter,
            order=pydantic_order,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
    )
    nodes = [Route.from_pydantic(item) for item in payload.items]
    edges = [RouteEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
    return RouteConnection(
        count=payload.total_count,
        edges=edges,
        page_info=PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
    )


@strawberry.field(description="Added in 25.19.0. Get a specific route by ID.")  # type: ignore[misc]
async def route(id: ID, info: Info[StrawberryGQLContext]) -> Route | None:
    """Get a specific route by ID."""
    _, route_id = resolve_global_id(id)

    route_info = await info.context.data_loaders.route_loader.load(UUID(route_id))
    if route_info is None:
        return None
    return Route.from_dataclass(route_info)


# Mutation resolvers


@strawberry.mutation(description="Added in 25.19.0. Update the traffic status of a route.")  # type: ignore[misc]
async def update_route_traffic_status(
    input: UpdateRouteTrafficStatusInputGQL,
    info: Info[StrawberryGQLContext],
) -> UpdateRouteTrafficStatusPayloadGQL:
    """Update route traffic status (ACTIVE/INACTIVE)."""
    _, route_id = resolve_global_id(input.route_id)

    processor = info.context.processors.deployment
    result = await processor.update_route_traffic_status.wait_for_complete(
        UpdateRouteTrafficStatusAction(
            route_id=UUID(route_id),
            traffic_status=RouteTrafficStatusEnum(input.traffic_status.value),
        )
    )

    return UpdateRouteTrafficStatusPayloadGQL(
        route=Route.from_dataclass(result.route),
    )
