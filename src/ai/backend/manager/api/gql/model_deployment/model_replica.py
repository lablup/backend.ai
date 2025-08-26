from datetime import datetime, timedelta
from enum import StrEnum
from typing import AsyncGenerator, Optional, cast
from uuid import UUID, uuid4

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID, PageInfo

from ai.backend.common.data.model_deployment.types import LivenessStatus as CommonLivenessStatus
from ai.backend.common.data.model_deployment.types import ReadinessStatus as CommonReadinessStatus
from ai.backend.manager.api.gql.base import JSONString, OrderDirection, StringFilter
from ai.backend.manager.api.gql.model_deployment.routing import (
    RoutingEdge,
    RoutingNode,
    RoutingNodeConnection,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext

from .model_revision import (
    ModelRevision,
    mock_model_revision_1,
)


@strawberry.enum(description="Added in 25.13.0")
class ReplicaStatus(StrEnum):
    HEALTHY = "HEALTHY"
    UNHEALTHY = "UNHEALTHY"


@strawberry.input(description="Added in 25.13.0")
class ReplicaStatusFilter:
    in_: Optional[list[ReplicaStatus]] = strawberry.field(name="in", default=None)
    equals: Optional[ReplicaStatus] = None


@strawberry.input(description="Added in 25.13.0")
class ReplicaFilter:
    name: Optional[StringFilter] = None
    status: Optional[ReplicaStatusFilter] = None

    AND: Optional[list["ReplicaFilter"]] = None
    OR: Optional[list["ReplicaFilter"]] = None
    NOT: Optional[list["ReplicaFilter"]] = None
    DISTINCT: Optional[bool] = None


@strawberry.enum(description="Added in 25.13.0")
class ReplicaOrderField(StrEnum):
    CREATED_AT = "CREATED_AT"
    NAME = "NAME"


@strawberry.input(description="Added in 25.13.0")
class ReplicaOrderBy:
    field: ReplicaOrderField
    direction: OrderDirection = OrderDirection.DESC


@strawberry.type(description="Added in 25.13.0")
class ModelReplica(Node):
    id: NodeID
    name: str
    status: ReplicaStatus
    revision: ModelRevision
    routings: RoutingNodeConnection


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
    name="llama-3-8b-instruct-replica-01",
    status=ReplicaStatus.HEALTHY,
    revision=mock_model_revision_1,
    routings=RoutingNodeConnection(
        count=1,
        edges=[
            RoutingEdge(
                node=RoutingNode(
                    id=UUID("60bf21b8-21a9-4655-aaeb-479a4ef02358"),
                    routing_id=uuid4(),
                    endpoint_url="https://api.backend.ai/models/dep-001/routing/01",
                    session_id=uuid4(),
                    readiness_status=CommonReadinessStatus.HEALTHY,
                    liveness_status=CommonLivenessStatus.HEALTHY,
                    weight=1,
                    detail=cast(JSONString, "{}"),
                    created_at=datetime.now() - timedelta(days=5),
                    live_stat=cast(
                        JSONString,
                        '{"requests": 1523, "latency_ms": 187, "tokens_per_second": 42.5}',
                    ),
                ),
                cursor="routing-cursor-1",
            )
        ],
        page_info=PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor="routing-cursor-1",
            end_cursor="routing-cursor-5",
        ),
    ),
)


mock_model_replica_2 = ModelReplica(
    id=UUID("7562e9d4-a368-4e28-9092-65eb91534bac"),
    name="llama-3-8b-instruct-replica-02",
    status=ReplicaStatus.HEALTHY,
    revision=mock_model_revision_1,
    routings=RoutingNodeConnection(
        count=1,
        edges=[
            RoutingEdge(
                node=RoutingNode(
                    id=UUID("21ede864-725d-4933-96f6-6df727f92217"),
                    routing_id=uuid4(),
                    endpoint_url="https://api.backend.ai/models/dep-001/routing/02",
                    session_id=uuid4(),
                    readiness_status=CommonReadinessStatus.HEALTHY,
                    liveness_status=CommonLivenessStatus.HEALTHY,
                    weight=2,
                    detail=cast(JSONString, "{}"),
                    created_at=datetime.now() - timedelta(days=5),
                    live_stat=cast(
                        JSONString,
                        '{"requests": 1456, "latency_ms": 195, "tokens_per_second": 41.2}',
                    ),
                ),
                cursor="token-cursor-2",
            )
        ],
        page_info=PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor="routing-cursor-2",
            end_cursor="routing-cursor-2",
        ),
    ),
)

mock_model_replica_3 = ModelReplica(
    id=UUID("2a2388ea-a312-422a-b77e-0e0b61c48145"),
    name="llama-3-8b-instruct-replica-03",
    status=ReplicaStatus.UNHEALTHY,
    revision=mock_model_revision_1,
    routings=RoutingNodeConnection(
        count=1,
        edges=[
            RoutingEdge(
                node=RoutingNode(
                    id=UUID("9613c8d1-53f1-4b8a-9cc4-6333d00afef0"),
                    routing_id=uuid4(),
                    endpoint_url="https://api.backend.ai/models/dep-001/routing/03",
                    session_id=uuid4(),
                    readiness_status=CommonReadinessStatus.NOT_CHECKED,
                    liveness_status=CommonLivenessStatus.HEALTHY,
                    weight=1,
                    detail=cast(JSONString, "{}"),
                    created_at=datetime.now() - timedelta(days=2),
                    live_stat=cast(
                        JSONString, '{"requests": 0, "latency_ms": 0, "tokens_per_second": 0}'
                    ),
                ),
                cursor="routing-cursor-3",
            ),
        ],
        page_info=PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor="routing-cursor-3",
            end_cursor="routing-cursor-3",
        ),
    ),
)


@strawberry.type(description="Added in 25.13.0")
class ReplicaStatusChangedPayload:
    replica: ModelReplica


@strawberry.field(description="Added in 25.13.0")
async def replica(id: ID) -> Optional[ModelReplica]:
    """Get a specific replica by ID."""

    return ModelReplica(
        id=id,
        name="llama-3-8b-instruct-replica-01",
        status=ReplicaStatus.HEALTHY,
        revision=mock_model_revision_1,
        routings=RoutingNodeConnection(
            count=1,
            edges=[
                RoutingEdge(
                    node=RoutingNode(
                        id=UUID("60bf21b8-21a9-4655-aaeb-479a4ef02358"),
                        routing_id=UUID("60bf21b8-21a9-4655-aaeb-479a4ef02358"),
                        endpoint_url="https://api.backend.ai/models/dep-001/routing/01",
                        session_id=uuid4(),
                        readiness_status=CommonReadinessStatus.NOT_CHECKED,
                        liveness_status=CommonLivenessStatus.HEALTHY,
                        weight=1,
                        detail=cast(JSONString, "{}"),
                        created_at=datetime.now() - timedelta(days=2),
                        live_stat=cast(
                            JSONString, '{"requests": 0, "latency_ms": 0, "tokens_per_second": 0}'
                        ),
                    ),
                    cursor="routing-cursor-1",
                ),
            ],
            page_info=PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor="routing-cursor-1",
                end_cursor="routing-cursor-1",
            ),
        ),
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
