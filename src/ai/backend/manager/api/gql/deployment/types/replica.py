"""GraphQL types for model replicas."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any, Self, cast
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.data.model_deployment.types import ActivenessStatus as CommonActivenessStatus
from ai.backend.common.data.model_deployment.types import LivenessStatus as CommonLivenessStatus
from ai.backend.common.data.model_deployment.types import ReadinessStatus as CommonReadinessStatus
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
from ai.backend.common.dto.manager.v2.deployment.response import (
    ReplicaStatusChangedPayload as ReplicaStatusChangedPayloadDTO,
)
from ai.backend.manager.api.gql.base import (
    OrderDirection,
    to_global_id,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_connection_type,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.session_federation import Session
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql_legacy.session import ComputeSessionNode
from ai.backend.manager.data.deployment.types import (
    ReplicaOrderField,
    RouteStatus,
    RouteTrafficStatus,
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


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
)
class ReplicaStatusFilter(PydanticInputMixin[ReplicaStatusFilterDTO]):
    in_: list[ReplicaStatus] | None = strawberry.field(name="in", default=None)
    equals: ReplicaStatus | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
)
class TrafficStatusFilter(PydanticInputMixin[ReplicaTrafficStatusFilterDTO]):
    in_: list[TrafficStatus] | None = strawberry.field(name="in", default=None)
    equals: TrafficStatus | None = None


# ========== ModelReplica Types ==========


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
    name="ReplicaFilter",
)
class ReplicaFilter(PydanticInputMixin[ReplicaFilterDTO]):
    status: ReplicaStatusFilter | None = None
    traffic_status: TrafficStatusFilter | None = None

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
)
class ReplicaOrderBy(PydanticInputMixin[ReplicaOrderDTO]):
    field: ReplicaOrderField
    direction: OrderDirection = OrderDirection.DESC


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="A single replica instance of a model deployment. Each replica runs in a separate compute session and serves inference requests. Replicas have health status indicators (readiness, liveness, activeness) and traffic weight for load balancing.",
    )
)
class ModelReplica(PydanticNodeMixin[ReplicaNodeDTO]):
    id: NodeID[str]
    session_id: ID
    revision_id: ID
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
            ComputeSessionNode, UUID(str(self.session_id)), is_target_graphene_object=True
        )
        return Session(id=ID(session_global_id))

    @strawberry.field
    async def revision(self, info: Info[StrawberryGQLContext]) -> ModelRevision:
        """Resolve revision by ID."""
        node = await info.context.adapters.deployment.get_revision(UUID(str(self.revision_id)))
        return ModelRevision.from_pydantic(node)

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
        return cast(list[Self | None], results)


ModelReplicaEdge = Edge[ModelReplica]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="A Relay-style connection for paginated access to model replicas. Includes total count for UI pagination display.",
    )
)
class ModelReplicaConnection(Connection[ModelReplica]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.19.0", description="Payload for replica status changed event."
    ),
    model=ReplicaStatusChangedPayloadDTO,
)
class ReplicaStatusChangedPayload:
    replica: ModelReplica
