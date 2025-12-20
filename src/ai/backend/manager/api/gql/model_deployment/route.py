"""GraphQL types, queries and mutations for routes."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from functools import lru_cache
from typing import Optional, override
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.common.exception import ModelDeploymentUnavailable
from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import (
    JSONString,
    OrderDirection,
    encode_cursor,
    resolve_global_id,
    to_global_id,
)
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext
from ai.backend.manager.data.deployment.types import (
    RouteInfo,
)
from ai.backend.manager.data.deployment.types import (
    RouteStatus as RouteStatusEnum,
)
from ai.backend.manager.data.deployment.types import (
    RouteTrafficStatus as RouteTrafficStatusEnum,
)
from ai.backend.manager.errors.deployment import EndpointNotFound
from ai.backend.manager.models.gql_models.session import ComputeSessionNode
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder
from ai.backend.manager.repositories.deployment.options import RouteConditions, RouteOrders
from ai.backend.manager.services.deployment.actions.route import (
    SearchRoutesAction,
    UpdateRouteTrafficStatusAction,
)

from .model_deployment import ModelDeployment
from .model_revision import ModelRevision

RouteStatusGQL = strawberry.enum(
    RouteStatusEnum,
    name="RouteStatus",
    description="Added in 25.19.0. Route status indicating the health and lifecycle state of a route.",
)

RouteTrafficStatusGQL = strawberry.enum(
    RouteTrafficStatusEnum,
    name="RouteTrafficStatus",
    description="Added in 25.19.0. Traffic routing status for a route. Controls whether traffic should be sent to this route.",
)


@strawberry.type(
    name="Route",
    description="Added in 25.19.0. Represents a route for a model deployment.",
)
class Route(Node):
    id: NodeID
    _deployment_id: strawberry.Private[UUID]
    _session_id: strawberry.Private[Optional[UUID]]
    _revision_id: strawberry.Private[Optional[UUID]]
    status: RouteStatusGQL = strawberry.field(
        description="The current status of the route indicating its health state.",
    )
    traffic_status: RouteTrafficStatusGQL = strawberry.field(
        description="The traffic routing status (ACTIVE/INACTIVE). Controls whether traffic should be sent to this route.",
    )
    traffic_ratio: float = strawberry.field(
        description="The traffic ratio for load balancing.",
    )
    created_at: datetime = strawberry.field(
        description="The timestamp when the route was created.",
    )
    error_data: Optional[JSONString] = strawberry.field(
        description="Error data if the route is in a failed state.",
    )

    @strawberry.field(description="The deployment this route belongs to.")
    async def deployment(self, info: Info[StrawberryGQLContext]) -> ModelDeployment:
        """Resolve deployment using dataloader."""
        deployment_data = await info.context.data_loaders.deployment_loader.load(
            self._deployment_id
        )
        if deployment_data is None:
            raise EndpointNotFound(extra_msg=f"id={self._deployment_id}")
        return ModelDeployment.from_dataclass(deployment_data)

    @strawberry.field(
        description="The session associated with the route. Can be null if the route is still provisioning."
    )
    async def session(self, info: Info[StrawberryGQLContext]) -> Optional[ID]:
        """Return session global ID if available."""
        if self._session_id is None:
            return None
        session_global_id = to_global_id(
            ComputeSessionNode, self._session_id, is_target_graphene_object=True
        )
        return ID(session_global_id)

    @strawberry.field(description="The revision associated with the route.")
    async def revision(self, info: Info[StrawberryGQLContext]) -> Optional[ModelRevision]:
        """Resolve revision using dataloader."""
        if self._revision_id is None:
            return None
        revision_data = await info.context.data_loaders.revision_loader.load(self._revision_id)
        if revision_data is None:
            return None
        return ModelRevision.from_dataclass(revision_data)

    @classmethod
    def from_dataclass(cls, data: RouteInfo) -> Route:
        return cls(
            id=ID(str(data.route_id)),
            _deployment_id=data.endpoint_id,
            _session_id=UUID(str(data.session_id)) if data.session_id else None,
            _revision_id=data.revision_id,
            status=RouteStatusGQL(data.status),
            traffic_status=RouteTrafficStatusGQL(data.traffic_status),
            traffic_ratio=data.traffic_ratio,
            created_at=data.created_at,
            error_data=JSONString.serialize(data.error_data) if data.error_data else None,
        )


RouteEdge = Edge[Route]


@strawberry.type(description="Added in 25.19.0. Connection type for paginated route results.")
class RouteConnection(Connection[Route]):
    count: int = strawberry.field(
        description="Total number of routes matching the filter criteria."
    )

    def __init__(self, *args, count: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.count = count


# Filter and OrderBy types


@strawberry.enum
class RouteOrderField(StrEnum):
    CREATED_AT = "created_at"
    STATUS = "status"
    TRAFFIC_RATIO = "traffic_ratio"


@strawberry.input(description="Added in 25.19.0. Filter for routes.")
class RouteFilter(GQLFilter):
    status: Optional[list[RouteStatusGQL]] = None
    traffic_status: Optional[list[RouteTrafficStatusGQL]] = None

    @override
    def build_conditions(self) -> list[QueryCondition]:
        """Build query conditions from this filter."""
        conditions: list[QueryCondition] = []

        if self.status:
            internal_statuses = [RouteStatusEnum(s.value) for s in self.status]
            conditions.append(RouteConditions.by_statuses(internal_statuses))

        if self.traffic_status:
            internal_traffic_statuses = [
                RouteTrafficStatusEnum(ts.value) for ts in self.traffic_status
            ]
            conditions.append(RouteConditions.by_traffic_statuses(internal_traffic_statuses))

        return conditions


@strawberry.input(description="Added in 25.19.0. Order by specification for routes.")
class RouteOrderBy(GQLOrderBy):
    field: RouteOrderField
    direction: OrderDirection = OrderDirection.ASC

    @override
    def to_query_order(self) -> QueryOrder:
        """Convert to repository QueryOrder."""
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case RouteOrderField.CREATED_AT:
                return RouteOrders.created_at(ascending)
            case RouteOrderField.STATUS:
                return RouteOrders.status(ascending)
            case RouteOrderField.TRAFFIC_RATIO:
                return RouteOrders.traffic_ratio(ascending)


# Pagination spec


@lru_cache(maxsize=1)
def _get_route_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=RouteOrders.created_at(ascending=False),
        backward_order=RouteOrders.created_at(ascending=True),
        forward_condition_factory=RouteConditions.by_cursor_forward,
        backward_condition_factory=RouteConditions.by_cursor_backward,
    )


# Input/Payload types for mutations


@strawberry.input(
    name="UpdateRouteTrafficStatusInput",
    description="Added in 25.19.0. Input for updating route traffic status.",
)
class UpdateRouteTrafficStatusInputGQL:
    route_id: ID = strawberry.field(description="The ID of the route to update.")
    traffic_status: RouteTrafficStatusGQL = strawberry.field(
        description="The new traffic status (ACTIVE/INACTIVE)."
    )


@strawberry.type(
    name="UpdateRouteTrafficStatusPayload",
    description="Added in 25.19.0. Result of updating route traffic status.",
)
class UpdateRouteTrafficStatusPayloadGQL:
    route: Route = strawberry.field(description="The updated route.")


# Query fields


@strawberry.field(description="Added in 25.19.0. Get a specific route by ID.")
async def route(id: ID, info: Info[StrawberryGQLContext]) -> Optional[Route]:
    """Get a specific route by ID."""
    _, route_id = resolve_global_id(id)

    route_info = await info.context.data_loaders.route_loader.load(UUID(route_id))
    if route_info is None:
        return None
    return Route.from_dataclass(route_info)


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

    processor = info.context.processors.deployment
    if processor is None:
        raise ModelDeploymentUnavailable(
            "Model Deployment feature is unavailable. Please contact support."
        )

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
        _get_route_pagination_spec(),
        filter=filter,
        order_by=order_by,
    )

    # Add deployment_id condition (always required)
    endpoint_uuid = UUID(endpoint_id)
    querier.conditions.insert(0, RouteConditions.by_endpoint_id(endpoint_uuid))

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


# Mutation fields


@strawberry.mutation(description="Added in 25.19.0. Update the traffic status of a route.")
async def update_route_traffic_status(
    input: UpdateRouteTrafficStatusInputGQL,
    info: Info[StrawberryGQLContext],
) -> UpdateRouteTrafficStatusPayloadGQL:
    """Update route traffic status (ACTIVE/INACTIVE)."""
    _, route_id = resolve_global_id(input.route_id)

    processor = info.context.processors.deployment
    if processor is None:
        raise ModelDeploymentUnavailable(
            "Model Deployment feature is unavailable. Please contact support."
        )

    result = await processor.update_route_traffic_status.wait_for_complete(
        UpdateRouteTrafficStatusAction(
            route_id=UUID(route_id),
            traffic_status=RouteTrafficStatusEnum(input.traffic_status.value),
        )
    )

    return UpdateRouteTrafficStatusPayloadGQL(
        route=Route.from_dataclass(result.route),
    )
