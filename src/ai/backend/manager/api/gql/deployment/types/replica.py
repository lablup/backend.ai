"""GraphQL types for model replicas."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any, Self
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, NodeID, PageInfo

from ai.backend.common.data.model_deployment.types import ActivenessStatus as CommonActivenessStatus
from ai.backend.common.data.model_deployment.types import LivenessStatus as CommonLivenessStatus
from ai.backend.common.data.model_deployment.types import ReadinessStatus as CommonReadinessStatus
from ai.backend.common.data.model_deployment.types import RouteStatus as CommonRouteStatus
from ai.backend.common.data.model_deployment.types import (
    RouteTrafficStatus as CommonRouteTrafficStatus,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    ReplicaFilter as ReplicaFilterDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    ReplicaOrder as ReplicaOrderDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    ReplicaStatusFilter as ReplicaStatusFilterDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    ReplicaTrafficStatusFilter as ReplicaTrafficStatusFilterDTO,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    ReplicaNode as ReplicaNodeDTO,
)
from ai.backend.common.dto.manager.v2.deployment.types import (
    OrderDirection as DTOOrderDirection,
)
from ai.backend.common.dto.manager.v2.deployment.types import (
    ReplicaOrderField as DTOReplicaOrderField,
)
from ai.backend.manager.api.gql.base import (
    OrderDirection,
    to_global_id,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.session_federation import Session
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql_legacy.session import ComputeSessionNode
from ai.backend.manager.data.deployment.types import (
    ModelReplicaData,
    ReplicaOrderField,
    RouteStatus,
    RouteTrafficStatus,
)
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


@strawberry.experimental.pydantic.input(
    model=ReplicaStatusFilterDTO,
    description="Added in 25.19.0",
)
class ReplicaStatusFilter:
    in_: list[ReplicaStatus] | None = strawberry.field(name="in", default=None)
    equals: ReplicaStatus | None = None

    def to_pydantic(self) -> ReplicaStatusFilterDTO:
        return ReplicaStatusFilterDTO(
            equals=CommonRouteStatus(self.equals.value) if self.equals else None,
            in_=[CommonRouteStatus(s.value) for s in self.in_] if self.in_ else None,
        )


@strawberry.experimental.pydantic.input(
    model=ReplicaTrafficStatusFilterDTO,
    description="Added in 25.19.0",
)
class TrafficStatusFilter:
    in_: list[TrafficStatus] | None = strawberry.field(name="in", default=None)
    equals: TrafficStatus | None = None

    def to_pydantic(self) -> ReplicaTrafficStatusFilterDTO:
        return ReplicaTrafficStatusFilterDTO(
            equals=CommonRouteTrafficStatus(self.equals.value) if self.equals else None,
            in_=[CommonRouteTrafficStatus(s.value) for s in self.in_] if self.in_ else None,
        )


# ========== ModelReplica Types ==========


@strawberry.experimental.pydantic.input(
    model=ReplicaFilterDTO,
    description="Added in 25.19.0",
)
class ReplicaFilter:
    status: ReplicaStatusFilter | None = None
    traffic_status: TrafficStatusFilter | None = None

    AND: list[ReplicaFilter] | None = None
    OR: list[ReplicaFilter] | None = None
    NOT: list[ReplicaFilter] | None = None

    def to_pydantic(self) -> ReplicaFilterDTO:
        return ReplicaFilterDTO(
            status=ReplicaStatusFilterDTO(
                equals=CommonRouteStatus(self.status.equals.value)
                if self.status and self.status.equals
                else None,
                in_=[CommonRouteStatus(s.value) for s in self.status.in_]
                if self.status and self.status.in_
                else None,
            )
            if self.status
            else None,
            traffic_status=ReplicaTrafficStatusFilterDTO(
                equals=CommonRouteTrafficStatus(self.traffic_status.equals.value)
                if self.traffic_status and self.traffic_status.equals
                else None,
                in_=[CommonRouteTrafficStatus(s.value) for s in self.traffic_status.in_]
                if self.traffic_status and self.traffic_status.in_
                else None,
            )
            if self.traffic_status
            else None,
            AND=[f.to_pydantic() for f in self.AND] if self.AND else None,
            OR=[f.to_pydantic() for f in self.OR] if self.OR else None,
            NOT=[f.to_pydantic() for f in self.NOT] if self.NOT else None,
        )


@strawberry.experimental.pydantic.input(
    model=ReplicaOrderDTO,
    description="Added in 25.19.0",
)
class ReplicaOrderBy:
    field: ReplicaOrderField
    direction: OrderDirection = OrderDirection.DESC

    def to_pydantic(self) -> ReplicaOrderDTO:
        return ReplicaOrderDTO(
            field=DTOReplicaOrderField(self.field.value.lower()),
            direction=DTOOrderDirection(self.direction.value.lower()),
        )


@strawberry.type
class ModelReplica(PydanticNodeMixin):
    """
    Added in 25.19.0.

    Represents a single replica instance of a model deployment. Each replica
    runs in a separate compute session and serves inference requests.

    Replicas have health status indicators (readiness, liveness, activeness)
    and traffic weight for load balancing.
    """

    id: NodeID[str]
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
    created_at: datetime = strawberry.field(description="Timestamp when the replica was created.")

    @strawberry.field(  # type: ignore[misc]
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
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.replica_loader.load_many([
            UUID(nid) for nid in node_ids
        ])
        return [cls.from_dataclass(data) if data is not None else None for data in results]

    @classmethod
    def from_dataclass(cls, data: ModelReplicaData) -> Self:
        return cls(
            id=ID(str(data.id)),
            _revision_id=data.revision_id,
            _session_id=data.session_id,
            readiness_status=ReadinessStatus(data.readiness_status),
            liveness_status=LivenessStatus(data.liveness_status),
            activeness_status=ActivenessStatus(data.activeness_status),
            weight=data.weight,
            created_at=data.created_at,
        )

    @classmethod
    def from_node(cls, node: ReplicaNodeDTO) -> Self:
        return cls(
            id=ID(str(node.id)),
            _revision_id=node.revision_id,
            _session_id=node.session_id,
            readiness_status=ReadinessStatus(node.readiness_status),
            liveness_status=LivenessStatus(node.liveness_status),
            activeness_status=ActivenessStatus(node.activeness_status),
            weight=node.weight,
            created_at=node.created_at,
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

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
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
