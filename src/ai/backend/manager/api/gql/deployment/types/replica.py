"""GraphQL types for model replicas."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import TYPE_CHECKING, Annotated, Any, Self, cast
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
from ai.backend.common.dto.manager.v2.deployment.types import (
    ReplicaOrderField,
)
from ai.backend.manager.api.gql.base import (
    OrderDirection,
    to_global_id,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_added_field,
    gql_connection_type,
    gql_enum,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.session_federation import Session
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql_legacy.session import ComputeSessionNode
from ai.backend.manager.data.deployment.types import (
    RouteHealthStatus,
    RouteStatus,
    RouteTrafficStatus,
)

from .revision import ModelRevision

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.deployment.types.deployment import ModelDeployment
    from ai.backend.manager.api.gql.session.types import SessionV2GQL

# ========== Enums ==========

ReadinessStatus: type[CommonReadinessStatus] = gql_enum(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="This enum represents the readiness status of a replica, indicating whether the deployment has been checked and its health state.",
    ),
    CommonReadinessStatus,
    name="ReadinessStatus",
)

LivenessStatus: type[CommonLivenessStatus] = gql_enum(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="This enum represents the liveness status of a replica, indicating whether the deployment is currently running and able to serve requests.",
    ),
    CommonLivenessStatus,
    name="LivenessStatus",
)

ActivenessStatus: type[CommonActivenessStatus] = gql_enum(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="This enum represents the activeness status of a replica, indicating whether the deployment is currently active and able to serve requests.",
    ),
    CommonActivenessStatus,
    name="ActivenessStatus",
)

ReplicaStatus: type[RouteStatus] = gql_enum(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="This enum represents the provisioning status of a replica.",
    ),
    RouteStatus,
    name="ReplicaStatus",
)

TrafficStatus: type[RouteTrafficStatus] = gql_enum(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="This enum represents the traffic status of a replica.",
    ),
    RouteTrafficStatus,
    name="TrafficStatus",
)

ReplicaHealthStatusGQL: type[RouteHealthStatus] = gql_enum(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="This enum represents the health check status of a replica.",
    ),
    RouteHealthStatus,
    name="ReplicaHealthStatus",
)


# ========== Status Filters ==========


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
)
class ReplicaStatusFilter(PydanticInputMixin[ReplicaStatusFilterDTO]):
    in_: list[ReplicaStatus] | None = gql_field(
        description="The in  field.", name="in", default=None
    )
    equals: ReplicaStatus | None = None
    not_in: list[ReplicaStatus] | None = gql_field(
        description="Excludes statuses in the list.", name="notIn", default=None
    )
    not_equals: ReplicaStatus | None = gql_field(
        description="Excludes exact status match.", name="notEquals", default=None
    )


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
)
class TrafficStatusFilter(PydanticInputMixin[ReplicaTrafficStatusFilterDTO]):
    in_: list[TrafficStatus] | None = gql_field(
        description="The in  field.", name="in", default=None
    )
    equals: TrafficStatus | None = None
    not_in: list[TrafficStatus] | None = gql_field(
        description="Excludes traffic statuses in the list.", name="notIn", default=None
    )
    not_equals: TrafficStatus | None = gql_field(
        description="Excludes exact traffic status match.", name="notEquals", default=None
    )


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
        description="A single replica instance of a model deployment. Each replica runs in a separate compute session and serves inference requests. Replicas have health status indicators (readiness, liveness, activeness).",
    )
)
class ModelReplica(PydanticNodeMixin[ReplicaNodeDTO]):
    id: NodeID[str]
    session_id: ID | None
    revision_id: ID
    deployment_id: ID = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="ID of the model deployment this replica belongs to.",
        )
    )
    readiness_status: ReadinessStatus = gql_field(
        description="Whether the replica has been checked and its health state."
    )
    liveness_status: LivenessStatus = gql_field(
        description="Whether the replica is currently running and able to serve requests."
    )
    activeness_status: ActivenessStatus = gql_field(
        description="Whether the replica is actively receiving traffic."
    )
    status: ReplicaStatus = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Provisioning status of the replica (mirrors the underlying route status).",
        )
    )
    traffic_status: TrafficStatus = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Traffic status of the replica.",
        )
    )
    health_status: ReplicaHealthStatusGQL = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Health check status of the replica.",
        )
    )
    created_at: datetime = gql_field(description="Timestamp when the replica was created.")

    @gql_field(
        description="The session associated with the replica. Can be null if the replica is still provisioning.",
        deprecation_reason="Use session_v2 instead.",
    )  # type: ignore[misc]
    async def session(self, info: Info[StrawberryGQLContext]) -> Session | None:
        if self.session_id is None:
            return None
        session_global_id = to_global_id(
            ComputeSessionNode, UUID(str(self.session_id)), is_target_graphene_object=True
        )
        return Session(id=ID(session_global_id))

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.3",
            description="The compute session running this replica, resolved via DataLoader.",
        )
    )  # type: ignore[misc]
    async def session_v2(
        self, info: Info[StrawberryGQLContext]
    ) -> (
        Annotated[
            SessionV2GQL,
            strawberry.lazy("ai.backend.manager.api.gql.session.types"),
        ]
        | None
    ):
        if self.session_id is None:
            return None
        from ai.backend.common.types import SessionId

        return await info.context.data_loaders.session_loader.load(
            SessionId(UUID(str(self.session_id)))
        )

    @gql_field(description="The revision of this entity.")  # type: ignore[misc]
    async def revision(self, info: Info[StrawberryGQLContext]) -> ModelRevision | None:
        """Resolve revision by ID using DataLoader."""
        result = await info.context.data_loaders.revision_loader.load(UUID(str(self.revision_id)))
        if result is None:
            raise ValueError(f"Revision not found: {self.revision_id}")
        return result

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="The model deployment this replica belongs to.",
        )
    )  # type: ignore[misc]
    async def deployment(
        self, info: Info[StrawberryGQLContext]
    ) -> (
        Annotated[
            ModelDeployment,
            strawberry.lazy("ai.backend.manager.api.gql.deployment.types.deployment"),
        ]
        | None
    ):
        return await info.context.data_loaders.deployment_loader.load(UUID(str(self.deployment_id)))

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
