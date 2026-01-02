"""GraphQL types for model replicas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, override
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID, PageInfo

from ai.backend.common.data.model_deployment.types import ActivenessStatus as CommonActivenessStatus
from ai.backend.common.data.model_deployment.types import LivenessStatus as CommonLivenessStatus
from ai.backend.common.data.model_deployment.types import ReadinessStatus as CommonReadinessStatus
from ai.backend.manager.api.gql.base import (
    JSONString,
    OrderDirection,
    to_global_id,
)
from ai.backend.manager.api.gql.session import Session
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext
from ai.backend.manager.data.deployment.types import (
    ModelReplicaData,
    ReplicaOrderField,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.models.gql_models.session import ComputeSessionNode
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder
from ai.backend.manager.repositories.deployment.options import RouteConditions, RouteOrders
from ai.backend.manager.services.deployment.actions.model_revision.get_revision_by_id import (
    GetRevisionByIdAction,
)

from .revision import ModelRevision

# ========== Enums ==========

ReadinessStatus: type[CommonReadinessStatus] = strawberry.enum(
    CommonReadinessStatus,
    name="ReadinessStatus",
    description="Added in 25.19.0. This enum represents the readiness status of a replica, indicating whether the deployment has been checked and its health state.",
)

LivenessStatus: type[CommonLivenessStatus] = strawberry.enum(
    CommonLivenessStatus,
    name="LivenessStatus",
    description="Added in 25.19.0. This enum represents the liveness status of a replica, indicating whether the deployment is currently running and able to serve requests.",
)

ActivenessStatus: type[CommonActivenessStatus] = strawberry.enum(
    CommonActivenessStatus,
    name="ActivenessStatus",
    description="Added in 25.19.0. This enum represents the activeness status of a replica, indicating whether the deployment is currently active and able to serve requests.",
)

ReplicaStatus: type[RouteStatus] = strawberry.enum(
    RouteStatus,
    name="ReplicaStatus",
    description="Added in 25.19.0. This enum represents the provisioning status of a replica.",
)

TrafficStatus: type[RouteTrafficStatus] = strawberry.enum(
    RouteTrafficStatus,
    name="TrafficStatus",
    description="Added in 25.19.0. This enum represents the traffic status of a replica.",
)


# ========== Status Filters ==========


@strawberry.input(description="Added in 25.19.0")
class ReplicaStatusFilter:
    in_: Optional[list[ReplicaStatus]] = strawberry.field(name="in", default=None)
    equals: Optional[ReplicaStatus] = None


@strawberry.input(description="Added in 25.19.0")
class TrafficStatusFilter:
    in_: Optional[list[TrafficStatus]] = strawberry.field(name="in", default=None)
    equals: Optional[TrafficStatus] = None


# ========== ModelReplica Types ==========


@strawberry.input(description="Added in 25.19.0")
class ReplicaFilter(GQLFilter):
    status: Optional[ReplicaStatusFilter] = None
    traffic_status: Optional[TrafficStatusFilter] = None

    AND: Optional[list[ReplicaFilter]] = None
    OR: Optional[list[ReplicaFilter]] = None
    NOT: Optional[list[ReplicaFilter]] = None

    @override
    def build_conditions(self) -> list[QueryCondition]:
        """Build query conditions from this filter."""
        conditions: list[QueryCondition] = []

        if self.status:
            if self.status.in_ is not None:
                statuses = [RouteStatus(s) for s in self.status.in_]
                conditions.append(RouteConditions.by_statuses(statuses))
            elif self.status.equals is not None:
                conditions.append(RouteConditions.by_statuses([RouteStatus(self.status.equals)]))

        if self.traffic_status:
            if self.traffic_status.in_ is not None:
                traffic_statuses = [RouteTrafficStatus(s) for s in self.traffic_status.in_]
                conditions.append(RouteConditions.by_traffic_statuses(traffic_statuses))
            elif self.traffic_status.equals is not None:
                conditions.append(
                    RouteConditions.by_traffic_statuses([
                        RouteTrafficStatus(self.traffic_status.equals)
                    ])
                )

        return conditions


@strawberry.input(description="Added in 25.19.0")
class ReplicaOrderBy(GQLOrderBy):
    field: ReplicaOrderField
    direction: OrderDirection = OrderDirection.DESC

    @override
    def to_query_order(self) -> QueryOrder:
        """Convert to repository QueryOrder."""
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case ReplicaOrderField.CREATED_AT:
                return RouteOrders.created_at(ascending)


@strawberry.type
class ModelReplica(Node):
    """
    Added in 25.19.0.

    Represents a single replica instance of a model deployment. Each replica
    runs in a separate compute session and serves inference requests.

    Replicas have health status indicators (readiness, liveness, activeness)
    and traffic weight for load balancing.
    """

    id: NodeID
    _session_id: strawberry.Private[UUID]
    _revision_id: strawberry.Private[UUID]
    readiness_status: ReadinessStatus = strawberry.field(
        description="Whether the replica has been checked and its health state.",
    )
    liveness_status: LivenessStatus = strawberry.field(
        description="Whether the replica is currently running and able to serve requests.",
    )
    activeness_status: ActivenessStatus = strawberry.field(
        description="Whether the replica is currently active and able to serve requests.",
    )
    weight: int = strawberry.field(
        description="Traffic weight for load balancing between replicas."
    )
    detail: JSONString = strawberry.field(
        description="Detailed information about the routing node including error or success messages."
    )
    created_at: datetime = strawberry.field(description="Timestamp when the replica was created.")
    live_stat: JSONString = strawberry.field(
        description="Live statistics of the routing node (CPU utilization, etc.)."
    )

    @strawberry.field(
        description="The session ID associated with the replica. This can be null right after replica creation."
    )
    async def session(self, info: Info[StrawberryGQLContext]) -> Session:
        session_global_id = to_global_id(
            ComputeSessionNode, self._session_id, is_target_graphene_object=True
        )
        return Session(id=ID(session_global_id))

    @strawberry.field
    async def revision(self, info: Info[StrawberryGQLContext]) -> ModelRevision:
        """Resolve revision by ID."""
        processor = info.context.processors.deployment
        result = await processor.get_revision_by_id.wait_for_complete(
            GetRevisionByIdAction(revision_id=self._revision_id)
        )
        return ModelRevision.from_dataclass(result.data)

    @classmethod
    def from_dataclass(cls, data: ModelReplicaData) -> ModelReplica:
        return cls(
            id=ID(str(data.id)),
            _revision_id=data.revision_id,
            _session_id=data.session_id,
            readiness_status=ReadinessStatus(data.readiness_status),
            liveness_status=LivenessStatus(data.liveness_status),
            activeness_status=ActivenessStatus(data.activeness_status),
            weight=data.weight,
            detail=JSONString.serialize(data.detail),
            created_at=data.created_at,
            live_stat=JSONString.serialize(data.live_stat),
        )


ModelReplicaEdge = Edge[ModelReplica]


@strawberry.type
class ModelReplicaConnection(Connection[ModelReplica]):
    """
    Added in 25.19.0.

    A Relay-style connection for paginated access to model replicas.
    Includes total count for UI pagination display.
    """

    count: int

    def __init__(self, *args, count: int, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.count = count

    @classmethod
    def from_dataclass(cls, replicas_data: list[ModelReplicaData]) -> ModelReplicaConnection:
        nodes = [ModelReplica.from_dataclass(data) for data in replicas_data]
        edges = [ModelReplicaEdge(node=node, cursor=str(node.id)) for node in nodes]

        page_info = PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        )

        return cls(count=len(nodes), edges=edges, page_info=page_info)


@strawberry.type(description="Added in 25.19.0")
class ReplicaStatusChangedPayload:
    replica: ModelReplica
