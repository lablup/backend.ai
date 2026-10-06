"""Route resolver functions."""

from __future__ import annotations

from strawberry import ID, Info
from strawberry.relay import PageInfo

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.replica import ReplicaID
from ai.backend.common.data.model_deployment.types import (
    RouteTrafficStatus as RouteTrafficStatusCommon,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    SearchRoutesInput,
)
from ai.backend.manager.api.gql.base import encode_cursor, resolve_entity_id, resolve_field_id
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
    gql_root_field,
)
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

# Query resolvers


@gql_root_field(
    BackendAIGQLMeta(
        added_version="25.19.0", description="List routes for a deployment with optional filters."
    )
)  # type: ignore[misc]
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
    endpoint_id = resolve_entity_id(deployment_id, DeploymentID)
    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_order = [o.to_pydantic() for o in order_by] if order_by else None
    payload = await info.context.adapters.deployment.search_routes(
<<<<<<< HEAD
        scope=RouteSearchScope(deployment_id=UUID(endpoint_id)),
=======
        scope=RouteOperationScope(deployment_id=endpoint_id),
>>>>>>> 9ff12c6cd (fix(BA-8122): answer a malformed GraphQL node id with a 400 instead of an internal error (#15257))
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


@gql_root_field(
    BackendAIGQLMeta(added_version="25.19.0", description="Get a specific route by ID.")
)  # type: ignore[misc]
async def route(id: ID, info: Info[StrawberryGQLContext]) -> Route | None:
    """Get a specific route by ID."""
    route_id = resolve_field_id(id, ReplicaID)
    return await info.context.data_loaders.route_loader.load(route_id)


# Mutation resolvers


@gql_mutation(
    BackendAIGQLMeta(added_version="25.19.0", description="Update the traffic status of a route")
)
async def update_route_traffic_status(
    input: UpdateRouteTrafficStatusInputGQL,
    info: Info[StrawberryGQLContext],
) -> UpdateRouteTrafficStatusPayloadGQL | None:
    """Update route traffic status (ACTIVE/INACTIVE)."""
    route_id = resolve_field_id(input.route_id, ReplicaID)
    route_node = await info.context.adapters.deployment.update_route_traffic(
        route_id,
        RouteTrafficStatusCommon(input.traffic_status.value),  # type: ignore[attr-defined]
    )
    return UpdateRouteTrafficStatusPayloadGQL(
        route=Route.from_pydantic(route_node),
    )
