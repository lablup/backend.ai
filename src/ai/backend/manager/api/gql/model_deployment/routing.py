from datetime import datetime
from uuid import UUID

import strawberry
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.common.data.model_deployment.types import LivenessStatus as CommonLivenessStatus
from ai.backend.common.data.model_deployment.types import ReadinessStatus as CommonReadinessStatus
from ai.backend.manager.api.gql.base import JSONString

ReadinessStatus = strawberry.enum(
    CommonReadinessStatus,
    name="ReadinessStatus",
    description="Added in 25.13.0. This enum represents the readiness status of a routing node, indicating whether the deployment has been checked and its health state.",
)

LivenessStatus = strawberry.enum(
    CommonLivenessStatus,
    name="LivenessStatus",
    description="Added in 25.13.0. This enum represents the liveness status of a routing node, indicating whether the deployment is currently running and able to serve requests.",
)


@strawberry.type(description="Added in 25.13.0")
class RoutingNode(Node):
    id: NodeID
    routing_id: UUID
    session_id: UUID
    readiness_status: ReadinessStatus = strawberry.field(
        description="Added in 25.13.0. This enum represents the readiness status of a routing node, indicating whether the deployment has been checked and its health state.",
    )
    liveness_status: LivenessStatus = strawberry.field(
        description="Added in 25.13.0. This enum represents the liveness status of a routing node, indicating whether the deployment is currently running and able to serve requests.",
    )
    weight: int
    detail: JSONString = strawberry.field(
        description="Detailed information about the routing node. It can include both error messages and success messages."
    )
    created_at: datetime
    live_stat: JSONString = strawberry.field(
        description='live statistics of the routing node. e.g. "live_stat": "{\\"cpu_util\\": {\\"current\\": \\"7.472\\", \\"capacity\\": \\"1000\\", \\"pct\\": \\"0.75\\", \\"unit_hint\\": \\"percent\\"}}"'
    )


RoutingEdge = Edge[RoutingNode]


@strawberry.type(description="Added in 25.13.0")
class RoutingNodeConnection(Connection[RoutingNode]):
    count: int

    def __init__(self, *args, count: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.count = count
