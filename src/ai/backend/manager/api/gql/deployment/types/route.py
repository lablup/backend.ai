"""Route GraphQL types for model deployment."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from functools import lru_cache
from typing import TYPE_CHECKING, Annotated, Any, Self
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, NodeID
from strawberry.scalars import JSON

from ai.backend.common.data.model_deployment.types import (
    RouteStatus as RouteStatusCommon,
)
from ai.backend.common.data.model_deployment.types import (
    RouteTrafficStatus as RouteTrafficStatusCommon,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    RouteFilter as RouteFilterDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    RouteOrder as RouteOrderDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    RouteStatusFilter as RouteStatusFilterDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    RouteTrafficStatusFilter as RouteTrafficStatusFilterDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    UpdateRouteTrafficStatusInput as UpdateRouteTrafficStatusInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    RouteNode as RouteNodeDTO,
)
from ai.backend.common.dto.manager.v2.deployment.types import (
    OrderDirection as DTOOrderDirection,
)
from ai.backend.common.dto.manager.v2.deployment.types import (
    RouteOrderField as DTORouteOrderField,
)
from ai.backend.manager.api.gql.adapter import PaginationSpec
from ai.backend.manager.api.gql.base import (
    OrderDirection,
    to_global_id,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql_legacy.session import ComputeSessionNode
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
from ai.backend.manager.models.routing.conditions import RouteConditions
from ai.backend.manager.models.routing.orders import RouteOrders
from ai.backend.manager.models.routing.row import RoutingRow

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.deployment.types.deployment import ModelDeployment
    from ai.backend.manager.api.gql.deployment.types.revision import ModelRevision

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
class Route(PydanticNodeMixin):
    id: NodeID[str]
    _deployment_id: strawberry.Private[UUID]
    _session_id: strawberry.Private[UUID | None]
    _revision_id: strawberry.Private[UUID | None]
    status: RouteStatusGQL = strawberry.field(
        description="The current status of the route indicating its health state.",
    )
    traffic_status: RouteTrafficStatusGQL = strawberry.field(
        description="The traffic routing status (ACTIVE/INACTIVE). Controls whether traffic should be sent to this route.",
    )
    traffic_ratio: float = strawberry.field(
        description="The traffic ratio for load balancing.",
    )
    created_at: datetime | None = strawberry.field(
        description="The timestamp when the route was created.",
    )
    error_data: JSON | None = strawberry.field(
        description="Error data if the route is in a failed state.",
    )

    @strawberry.field(description="The deployment this route belongs to.")  # type: ignore[misc]
    async def deployment(
        self, info: Info[StrawberryGQLContext]
    ) -> Annotated[ModelDeployment, strawberry.lazy(".deployment")]:
        """Resolve deployment using dataloader."""
        from ai.backend.manager.api.gql.deployment.types.deployment import ModelDeployment

        deployment_data = await info.context.data_loaders.deployment_loader.load(
            self._deployment_id
        )
        if deployment_data is None:
            raise EndpointNotFound(extra_msg=f"id={self._deployment_id}")
        return ModelDeployment.from_dataclass(deployment_data)

    @strawberry.field(  # type: ignore[misc]
        description="The session associated with the route. Can be null if the route is still provisioning."
    )
    async def session(self, info: Info[StrawberryGQLContext]) -> ID | None:
        """Return session global ID if available."""
        if self._session_id is None:
            return None
        session_global_id = to_global_id(
            ComputeSessionNode, self._session_id, is_target_graphene_object=True
        )
        return ID(session_global_id)

    @strawberry.field(description="The revision associated with the route.")  # type: ignore[misc]
    async def revision(
        self, info: Info[StrawberryGQLContext]
    ) -> Annotated[ModelRevision, strawberry.lazy(".revision")] | None:
        """Resolve revision using dataloader."""
        from ai.backend.manager.api.gql.deployment.types.revision import ModelRevision

        if self._revision_id is None:
            return None
        revision_data = await info.context.data_loaders.revision_loader.load(self._revision_id)
        if revision_data is None:
            return None
        return ModelRevision.from_dataclass(revision_data)

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
        return [cls.from_dataclass(data) if data is not None else None for data in results]

    @classmethod
    def from_dataclass(cls, data: RouteInfo) -> Self:
        return cls(
            id=ID(str(data.route_id)),
            _deployment_id=data.endpoint_id,
            _session_id=UUID(str(data.session_id)) if data.session_id else None,
            _revision_id=data.revision_id,
            status=RouteStatusGQL(data.status),
            traffic_status=RouteTrafficStatusGQL(data.traffic_status),
            traffic_ratio=data.traffic_ratio,
            created_at=data.created_at,
            error_data=data.error_data,
        )

    @classmethod
    def from_node(cls, node: RouteNodeDTO) -> Self:
        return cls(
            id=ID(str(node.id)),
            _deployment_id=node.endpoint_id,
            _session_id=UUID(node.session_id) if node.session_id else None,
            _revision_id=node.revision_id,
            status=RouteStatusGQL(RouteStatusEnum(node.status.value)),
            traffic_status=RouteTrafficStatusGQL(RouteTrafficStatusEnum(node.traffic_status.value)),
            traffic_ratio=node.traffic_ratio,
            created_at=node.created_at,
            error_data=node.error_data,
        )


RouteEdge = Edge[Route]


@strawberry.type(description="Added in 25.19.0. Connection type for paginated route results.")
class RouteConnection(Connection[Route]):
    count: int = strawberry.field(
        description="Total number of routes matching the filter criteria."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# Filter and OrderBy types


@strawberry.experimental.pydantic.input(
    model=RouteStatusFilterDTO,
    name="RouteStatusFilter",
    description="Added in 26.3.0. Filter for route status with equality and membership operators.",
)
class RouteStatusFilterGQL:
    equals: RouteStatusGQL | None = strawberry.field(
        default=None, description="Matches routes with this exact status."
    )
    in_: list[RouteStatusGQL] | None = strawberry.field(
        name="in", default=None, description="Matches routes whose status is in this list."
    )
    not_equals: RouteStatusGQL | None = strawberry.field(
        default=None, description="Excludes routes with this exact status."
    )
    not_in: list[RouteStatusGQL] | None = strawberry.field(
        default=None, description="Excludes routes whose status is in this list."
    )

    def to_pydantic(self) -> RouteStatusFilterDTO:
        return RouteStatusFilterDTO(
            equals=RouteStatusCommon(self.equals.value) if self.equals else None,
            in_=[RouteStatusCommon(s.value) for s in self.in_] if self.in_ else None,
            not_equals=RouteStatusCommon(self.not_equals.value) if self.not_equals else None,
            not_in=[RouteStatusCommon(s.value) for s in self.not_in] if self.not_in else None,
        )


@strawberry.experimental.pydantic.input(
    model=RouteTrafficStatusFilterDTO,
    name="RouteTrafficStatusFilter",
    description="Added in 26.3.0. Filter for route traffic status with equality and membership operators.",
)
class RouteTrafficStatusFilterGQL:
    equals: RouteTrafficStatusGQL | None = strawberry.field(
        default=None, description="Matches routes with this exact traffic status."
    )
    in_: list[RouteTrafficStatusGQL] | None = strawberry.field(
        name="in", default=None, description="Matches routes whose traffic status is in this list."
    )
    not_equals: RouteTrafficStatusGQL | None = strawberry.field(
        default=None, description="Excludes routes with this exact traffic status."
    )
    not_in: list[RouteTrafficStatusGQL] | None = strawberry.field(
        default=None, description="Excludes routes whose traffic status is in this list."
    )

    def to_pydantic(self) -> RouteTrafficStatusFilterDTO:
        return RouteTrafficStatusFilterDTO(
            equals=RouteTrafficStatusCommon(self.equals.value) if self.equals else None,
            in_=[RouteTrafficStatusCommon(s.value) for s in self.in_] if self.in_ else None,
            not_equals=RouteTrafficStatusCommon(self.not_equals.value) if self.not_equals else None,
            not_in=[RouteTrafficStatusCommon(s.value) for s in self.not_in]
            if self.not_in
            else None,
        )


@strawberry.enum
class RouteOrderField(StrEnum):
    CREATED_AT = "created_at"
    STATUS = "status"
    TRAFFIC_RATIO = "traffic_ratio"


@strawberry.experimental.pydantic.input(
    model=RouteFilterDTO,
    description="Added in 25.19.0. Filter for routes.",
)
class RouteFilter:
    status: RouteStatusFilterGQL | None = None
    traffic_status: RouteTrafficStatusFilterGQL | None = None

    AND: list[RouteFilter] | None = None
    OR: list[RouteFilter] | None = None
    NOT: list[RouteFilter] | None = None

    def to_pydantic(self) -> RouteFilterDTO:
        return RouteFilterDTO(
            status=RouteStatusFilterDTO(
                equals=RouteStatusCommon(self.status.equals.value) if self.status.equals else None,
                in_=[RouteStatusCommon(s.value) for s in self.status.in_]
                if self.status.in_
                else None,
                not_equals=RouteStatusCommon(self.status.not_equals.value)
                if self.status.not_equals
                else None,
                not_in=[RouteStatusCommon(s.value) for s in self.status.not_in]
                if self.status.not_in
                else None,
            )
            if self.status
            else None,
            traffic_status=RouteTrafficStatusFilterDTO(
                equals=RouteTrafficStatusCommon(self.traffic_status.equals.value)
                if self.traffic_status.equals
                else None,
                in_=[RouteTrafficStatusCommon(s.value) for s in self.traffic_status.in_]
                if self.traffic_status.in_
                else None,
                not_equals=RouteTrafficStatusCommon(self.traffic_status.not_equals.value)
                if self.traffic_status.not_equals
                else None,
                not_in=[RouteTrafficStatusCommon(s.value) for s in self.traffic_status.not_in]
                if self.traffic_status.not_in
                else None,
            )
            if self.traffic_status
            else None,
            AND=[f.to_pydantic() for f in self.AND] if self.AND else None,
            OR=[f.to_pydantic() for f in self.OR] if self.OR else None,
            NOT=[f.to_pydantic() for f in self.NOT] if self.NOT else None,
        )


@strawberry.experimental.pydantic.input(
    model=RouteOrderDTO,
    description="Added in 25.19.0. Order by specification for routes.",
)
class RouteOrderBy:
    field: RouteOrderField
    direction: OrderDirection = OrderDirection.ASC

    def to_pydantic(self) -> RouteOrderDTO:
        return RouteOrderDTO(
            field=DTORouteOrderField(self.field.value),
            direction=DTOOrderDirection(self.direction.value.lower()),
        )


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


@strawberry.experimental.pydantic.input(
    model=UpdateRouteTrafficStatusInputDTO,
    name="UpdateRouteTrafficStatusInput",
    description="Added in 25.19.0. Input for updating route traffic status.",
)
class UpdateRouteTrafficStatusInputGQL:
    route_id: ID = strawberry.field(description="The ID of the route to update.")
    traffic_status: RouteTrafficStatusGQL = strawberry.field(
        description="The new traffic status (ACTIVE/INACTIVE)."
    )

    def to_pydantic(self) -> UpdateRouteTrafficStatusInputDTO:
        return UpdateRouteTrafficStatusInputDTO(
            route_id=UUID(self.route_id),
            traffic_status=RouteTrafficStatusCommon(self.traffic_status.value),
        )


@strawberry.type(
    name="UpdateRouteTrafficStatusPayload",
    description="Added in 25.19.0. Result of updating route traffic status.",
)
class UpdateRouteTrafficStatusPayloadGQL:
    route: Route = strawberry.field(description="The updated route.")
