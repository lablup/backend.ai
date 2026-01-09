"""Route resolver functions."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

import strawberry
from strawberry import ID, Info

from ai.backend.manager.api.gql.base import resolve_global_id
from ai.backend.manager.api.gql.deployment.fetcher.route import fetch_routes
from ai.backend.manager.api.gql.deployment.types.route import (
    Route,
    RouteConnection,
    RouteFilter,
    RouteOrderBy,
    UpdateRouteTrafficStatusInputGQL,
    UpdateRouteTrafficStatusPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.data.deployment.types import RouteTrafficStatus as RouteTrafficStatusEnum
from ai.backend.manager.repositories.deployment.options import RouteConditions
from ai.backend.manager.services.deployment.actions.route import (
    UpdateRouteTrafficStatusAction,
)

# Query resolvers


@strawberry.field(
    description="Added in 25.19.0. List routes for a deployment with optional filters."
)
async def routes(
    info: Info[StrawberryGQLContext],
    deployment_id: ID,
    filter: Optional[RouteFilter] = None,
    order_by: Optional[list[RouteOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> RouteConnection:
    """List routes for a deployment with optional filters."""
    _, endpoint_id = resolve_global_id(deployment_id)
    return await fetch_routes(
        info=info,
        filter=filter,
        order_by=order_by,
        before=before,
        after=after,
        first=first,
        last=last,
        limit=limit,
        offset=offset,
        base_conditions=[RouteConditions.by_endpoint_id(UUID(endpoint_id))],
    )


@strawberry.field(description="Added in 25.19.0. Get a specific route by ID.")
async def route(id: ID, info: Info[StrawberryGQLContext]) -> Optional[Route]:
    """Get a specific route by ID."""
    _, route_id = resolve_global_id(id)

    route_info = await info.context.data_loaders.route_loader.load(UUID(route_id))
    if route_info is None:
        return None
    return Route.from_dataclass(route_info)


# Mutation resolvers


@strawberry.mutation(description="Added in 25.19.0. Update the traffic status of a route.")
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
