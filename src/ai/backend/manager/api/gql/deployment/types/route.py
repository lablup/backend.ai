"""Route GraphQL types for model deployment."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from functools import lru_cache
from typing import TYPE_CHECKING, Annotated, Any, Self, cast
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, NodeID
from strawberry.scalars import JSON

from ai.backend.common.dto.manager.v2.deployment.request import (
    RouteFilter as RouteFilterDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    RouteOrder as RouteOrderDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    UpdateRouteTrafficStatusInput as UpdateRouteTrafficStatusInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    RouteNode as RouteNodeDTO,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    UpdateRouteTrafficStatusPayload as UpdateRouteTrafficStatusPayloadDTO,
)
from ai.backend.manager.api.gql.adapter import PaginationSpec
from ai.backend.manager.api.gql.base import (
    OrderDirection,
    to_global_id,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_connection_type,
    gql_enum,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql_legacy.session import ComputeSessionNode
from ai.backend.manager.data.deployment.types import (
    RouteHealthStatus as RouteHealthStatusEnum,
)
from ai.backend.manager.data.deployment.types import (
    RouteStatus as RouteStatusEnum,
)
from ai.backend.manager.data.deployment.types import (
    RouteTrafficStatus as RouteTrafficStatusEnum,
)
from ai.backend.manager.errors.deployment import EndpointNotFound
from ai.backend.manager.models.routing.conditions import RouteConditions
from ai.backend.manager.models.routing.orders import RouteOrders
from ai.backend.manager.models.routing.row import RoutingRow

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.deployment.types.deployment import ModelDeployment
    from ai.backend.manager.api.gql.deployment.types.revision import ModelRevision


RouteStatusGQL: type[RouteStatusEnum] = gql_enum(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="Lifecycle status of a route.",
    ),
    RouteStatusEnum,
    name="RouteStatus",
)

RouteHealthStatusGQL: type[RouteHealthStatusEnum] = gql_enum(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="Health check status of a route.",
    ),
    RouteHealthStatusEnum,
    name="RouteHealthStatus",
)

RouteTrafficStatusGQL: type[RouteTrafficStatusEnum] = gql_enum(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="Traffic routing status for a route. Controls whether traffic should be sent to this route.",
    ),
    RouteTrafficStatusEnum,
    name="RouteTrafficStatus",
)


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.19.0", description="Represents a route for a model deployment."
    ),
    name="Route",
)
class Route(PydanticNodeMixin[RouteNodeDTO]):
    id: NodeID[str]
    deployment_id: ID
    session_id: ID | None
    revision_id: ID | None
    status: RouteStatusGQL = gql_field(description="The lifecycle status of the route.")
    health_status: RouteHealthStatusGQL = gql_field(
        description="The health check status of the route."
    )
    traffic_status: RouteTrafficStatusGQL = gql_field(
        description="The traffic routing status (ACTIVE/INACTIVE). Controls whether traffic should be sent to this route."
    )
    traffic_ratio: float = gql_field(description="The traffic ratio for load balancing.")
    created_at: datetime | None = gql_field(description="The timestamp when the route was created.")
    error_data: JSON | None = gql_field(description="Error data if the route is in a failed state.")

    @gql_field(description="The deployment this route belongs to.")  # type: ignore[misc]
    async def deployment(
        self, info: Info[StrawberryGQLContext]
    ) -> Annotated[ModelDeployment, strawberry.lazy(".deployment")]:
        """Resolve deployment using dataloader."""
        deployment_id = UUID(str(self.deployment_id))
        deployment_data = await info.context.data_loaders.deployment_loader.load(deployment_id)
        if deployment_data is None:
            raise EndpointNotFound(extra_msg=f"id={deployment_id}")
        return deployment_data

    @gql_field(
        description="The session associated with the route. Can be null if the route is still provisioning."
    )  # type: ignore[misc]
    async def session(self, info: Info[StrawberryGQLContext]) -> ID | None:
        """Return session global ID if available."""
        if self.session_id is None:
            return None
        session_global_id = to_global_id(
            ComputeSessionNode, UUID(str(self.session_id)), is_target_graphene_object=True
        )
        return ID(session_global_id)

    @gql_field(description="The revision associated with the route.")  # type: ignore[misc]
    async def revision(
        self, info: Info[StrawberryGQLContext]
    ) -> Annotated[ModelRevision, strawberry.lazy(".revision")] | None:
        """Resolve revision using dataloader."""
        if self.revision_id is None:
            return None
        return await info.context.data_loaders.revision_loader.load(UUID(str(self.revision_id)))

    @classmethod
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.route_loader.load_many([
            UUID(nid) for nid in node_ids
        ])
        return cast(list[Self | None], results)


RouteEdge = Edge[Route]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="25.19.0", description="Connection type for paginated route results."
    )
)
class RouteConnection(Connection[Route]):
    count: int = gql_field(description="Total number of routes matching the filter criteria.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# Filter and OrderBy types


@gql_enum(
    BackendAIGQLMeta(added_version="25.19.0", description="Fields available for ordering routes")
)
class RouteOrderField(StrEnum):
    CREATED_AT = "created_at"
    STATUS = "status"
    TRAFFIC_RATIO = "traffic_ratio"


@gql_pydantic_input(
    BackendAIGQLMeta(description="Filter for routes.", added_version="25.19.0"),
    name="RouteFilter",
)
class RouteFilter(PydanticInputMixin[RouteFilterDTO]):
    status: list[RouteStatusGQL] | None = None
    health_status: list[RouteHealthStatusGQL] | None = None
    traffic_status: list[RouteTrafficStatusGQL] | None = None

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(description="Order by specification for routes.", added_version="25.19.0"),
)
class RouteOrderBy(PydanticInputMixin[RouteOrderDTO]):
    field: RouteOrderField
    direction: OrderDirection = OrderDirection.ASC


# Pagination spec


@lru_cache(maxsize=1)
def get_route_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=RouteOrders.created_at(ascending=False),
        backward_order=RouteOrders.created_at(ascending=True),
        forward_condition_factory=RouteConditions.by_cursor_forward,
        backward_condition_factory=RouteConditions.by_cursor_backward,
        tiebreaker_order=RoutingRow.id.asc(),
    )


# Input/Payload types for mutations


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for updating route traffic status.", added_version="25.19.0"
    ),
    name="UpdateRouteTrafficStatusInput",
)
class UpdateRouteTrafficStatusInputGQL(PydanticInputMixin[UpdateRouteTrafficStatusInputDTO]):
    route_id: ID = gql_field(description="The ID of the route to update.")
    traffic_status: RouteTrafficStatusGQL = gql_field(
        description="The new traffic status (ACTIVE/INACTIVE)."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.19.0", description="Result of updating route traffic status."
    ),
    model=UpdateRouteTrafficStatusPayloadDTO,
    name="UpdateRouteTrafficStatusPayload",
)
class UpdateRouteTrafficStatusPayloadGQL:
    route: Route
