from datetime import datetime, timedelta
from enum import StrEnum
from typing import AsyncGenerator, Optional, cast
from uuid import UUID, uuid4

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID, PageInfo

from ai.backend.common.data.model_deployment.types import ActivenessStatus as CommonActivenessStatus
from ai.backend.common.data.model_deployment.types import LivenessStatus as CommonLivenessStatus
from ai.backend.common.data.model_deployment.types import ReadinessStatus as CommonReadinessStatus
from ai.backend.manager.api.gql.base import JSONString, OrderDirection
from ai.backend.manager.api.gql.session import Session
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.models.gql_relay import AsyncNode

from .model_revision import (
    ModelRevision,
    mock_model_revision_1,
)

ReadinessStatus = strawberry.enum(
    CommonReadinessStatus,
    name="ReadinessStatus",
    description="Added in 25.13.0. This enum represents the readiness status of a replica, indicating whether the deployment has been checked and its health state.",
)

LivenessStatus = strawberry.enum(
    CommonLivenessStatus,
    name="LivenessStatus",
    description="Added in 25.13.0. This enum represents the liveness status of a replica, indicating whether the deployment is currently running and able to serve requests.",
)

ActivenessStatus = strawberry.enum(
    CommonActivenessStatus,
    name="ActivenessStatus",
    description="Added in 25.13.0. This enum represents the activeness status of a replica, indicating whether the deployment is currently active and able to serve requests.",
)


@strawberry.input(description="Added in 25.13.0")
class ReadinessStatusFilter:
    in_: Optional[list[ReadinessStatus]] = strawberry.field(name="in", default=None)
    equals: Optional[ReadinessStatus] = None


@strawberry.input(description="Added in 25.13.0")
class LivenessStatusFilter:
    in_: Optional[list[LivenessStatus]] = strawberry.field(name="in", default=None)
    equals: Optional[LivenessStatus] = None


@strawberry.input(description="Added in 25.13.0")
class ActivenessStatusFilter:
    in_: Optional[list[ActivenessStatus]] = strawberry.field(name="in", default=None)
    equals: Optional[ActivenessStatus] = None


@strawberry.input(description="Added in 25.13.0")
class ReplicaFilter:
    readiness_status: Optional[ReadinessStatusFilter] = None
    liveness_status: Optional[LivenessStatusFilter] = None
    activeness_status: Optional[ActivenessStatusFilter] = None
    id: Optional[UUID] = None

    AND: Optional[list["ReplicaFilter"]] = None
    OR: Optional[list["ReplicaFilter"]] = None
    NOT: Optional[list["ReplicaFilter"]] = None


@strawberry.enum(description="Added in 25.13.0")
class ReplicaOrderField(StrEnum):
    CREATED_AT = "CREATED_AT"


@strawberry.input(description="Added in 25.13.0")
class ReplicaOrderBy:
    field: ReplicaOrderField
    direction: OrderDirection = OrderDirection.DESC


@strawberry.type(description="Added in 25.13.0")
class ModelReplica(Node):
    id: NodeID
    revision: ModelRevision
    _session_id: strawberry.Private[UUID]

    @strawberry.field(
        description="The session ID associated with the replica. This can be null right after replica creation."
    )
    async def session(self, info: Info[StrawberryGQLContext]) -> "Session":
        session_global_id = AsyncNode.to_global_id("ComputeSessionNode", self._session_id)
        return Session(id=ID(session_global_id))

    readiness_status: ReadinessStatus = strawberry.field(
        description="This represents whether the replica has been checked and its health state.",
    )
    liveness_status: LivenessStatus = strawberry.field(
        description="This represents whether the replica is currently running and able to serve requests.",
    )
    activeness_status: ActivenessStatus = strawberry.field(
        description="This represents whether the replica is currently active and able to serve requests.",
    )
    weight: int
    detail: JSONString = strawberry.field(
        description="Detailed information about the routing node. It can include both error messages and success messages."
    )
    created_at: datetime
    live_stat: JSONString = strawberry.field(
        description='live statistics of the routing node. e.g. "live_stat": "{\\"cpu_util\\": {\\"current\\": \\"7.472\\", \\"capacity\\": \\"1000\\", \\"pct\\": \\"0.75\\", \\"unit_hint\\": \\"percent\\"}}"'
    )


ModelReplicaEdge = Edge[ModelReplica]


@strawberry.type(description="Added in 25.13.0")
class ModelReplicaConnection(Connection[ModelReplica]):
    count: int

    def __init__(self, *args, count: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.count = count


# Mock Model Replicas
mock_model_replica_1 = ModelReplica(
    id=UUID("b62f9890-228a-40c9-a614-63387805b9a7"),
    revision=mock_model_revision_1,
    _session_id=uuid4(),
    readiness_status=CommonReadinessStatus.HEALTHY,
    liveness_status=CommonLivenessStatus.HEALTHY,
    activeness_status=CommonActivenessStatus.ACTIVE,
    weight=1,
    detail=cast(
        JSONString,
        '{"type": "creation_success", "message": "Model replica created successfully", "status": "operational"}',
    ),
    created_at=datetime.now() - timedelta(days=5),
    live_stat=cast(
        JSONString,
        '{"requests": 1523, "latency_ms": 187, "tokens_per_second": 42.5}',
    ),
)


mock_model_replica_2 = ModelReplica(
    id=UUID("7562e9d4-a368-4e28-9092-65eb91534bac"),
    revision=mock_model_revision_1,
    _session_id=uuid4(),
    readiness_status=CommonReadinessStatus.HEALTHY,
    liveness_status=CommonLivenessStatus.HEALTHY,
    activeness_status=CommonActivenessStatus.ACTIVE,
    weight=2,
    detail=cast(
        JSONString,
        '{"type": "creation_success", "message": "Model replica created successfully", "status": "operational"}',
    ),
    created_at=datetime.now() - timedelta(days=5),
    live_stat=cast(
        JSONString,
        '{"requests": 1456, "latency_ms": 195, "tokens_per_second": 41.2}',
    ),
)

mock_model_replica_3 = ModelReplica(
    id=UUID("2a2388ea-a312-422a-b77e-0e0b61c48145"),
    revision=mock_model_revision_1,
    _session_id=uuid4(),
    readiness_status=CommonReadinessStatus.UNHEALTHY,
    liveness_status=CommonLivenessStatus.HEALTHY,
    activeness_status=CommonActivenessStatus.INACTIVE,
    weight=0,
    detail=cast(
        JSONString,
        '{"type": "creation_failed", "errors": [{"src": "", "name": "InvalidAPIParameters", "repr": "<InvalidAPIParameters(400): Missing or invalid API parameters. (`mount-in-session` Not allowed in vfolder host(`seoul-h100:flash02`))>"}]}',
    ),
    created_at=datetime.now() - timedelta(days=2),
    live_stat=cast(JSONString, '{"requests": 0, "latency_ms": 0, "tokens_per_second": 0}'),
)


@strawberry.type(description="Added in 25.13.0")
class ReplicaStatusChangedPayload:
    replica: ModelReplica


@strawberry.field(description="Added in 25.13.0")
async def replica(id: ID, info: Info[StrawberryGQLContext]) -> Optional[ModelReplica]:
    """Get a specific replica by ID."""

    return ModelReplica(
        id=id,
        revision=mock_model_revision_1,
        _session_id=uuid4(),
        readiness_status=CommonReadinessStatus.NOT_CHECKED,
        liveness_status=CommonLivenessStatus.HEALTHY,
        activeness_status=CommonActivenessStatus.ACTIVE,
        weight=1,
        detail=cast(JSONString, "{}"),
        created_at=datetime.now() - timedelta(days=2),
        live_stat=cast(JSONString, '{"requests": 0, "latency_ms": 0, "tokens_per_second": 0}'),
    )


async def resolve_replicas(
    info: Info[StrawberryGQLContext],
    filter: Optional[ReplicaFilter] = None,
    order_by: Optional[list[ReplicaOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> ModelReplicaConnection:
    return ModelReplicaConnection(
        count=3,
        edges=[
            ModelReplicaEdge(node=mock_model_replica_1, cursor="replica-cursor-1"),
            ModelReplicaEdge(node=mock_model_replica_2, cursor="replica-cursor-2"),
            ModelReplicaEdge(node=mock_model_replica_3, cursor="replica-cursor-3"),
        ],
        page_info=PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor="replica-cursor-1",
            end_cursor="replica-cursor-3",
        ),
    )


@strawberry.field(description="Added in 25.13.0")
async def replicas(
    info: Info[StrawberryGQLContext],
    filter: Optional[ReplicaFilter] = None,
    order_by: Optional[list[ReplicaOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> ModelReplicaConnection:
    return await resolve_replicas(
        info=info,
        filter=filter,
        order_by=order_by,
        before=before,
        after=after,
        first=first,
        last=last,
        limit=limit,
        offset=offset,
    )


@strawberry.subscription(description="Added in 25.13.0")
async def replica_status_changed(
    revision_id: ID,
) -> AsyncGenerator[ReplicaStatusChangedPayload, None]:
    """Subscribe to replica status changes."""
    replicas = [mock_model_replica_1, mock_model_replica_2, mock_model_replica_3]

    for replica in replicas:
        yield ReplicaStatusChangedPayload(replica=replica)
