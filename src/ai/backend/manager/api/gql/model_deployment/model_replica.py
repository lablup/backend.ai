from collections.abc import Sequence
from datetime import datetime
from functools import lru_cache
from typing import AsyncGenerator, Optional, override
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID, PageInfo

from ai.backend.common.data.model_deployment.types import ActivenessStatus as CommonActivenessStatus
from ai.backend.common.data.model_deployment.types import LivenessStatus as CommonLivenessStatus
from ai.backend.common.data.model_deployment.types import ReadinessStatus as CommonReadinessStatus
from ai.backend.common.exception import ModelDeploymentUnavailable
from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import (
    JSONString,
    OrderDirection,
    resolve_global_id,
    to_global_id,
)
from ai.backend.manager.api.gql.session import Session
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext
from ai.backend.manager.data.deployment.types import ModelReplicaData, ReplicaOrderField
from ai.backend.manager.models.gql_models.session import ComputeSessionNode
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder
from ai.backend.manager.repositories.deployment.options import RouteConditions, RouteOrders
from ai.backend.manager.repositories.deployment.types.types import (
    ActivenessStatusFilter as RepoActivenessStatus,
)
from ai.backend.manager.repositories.deployment.types.types import (
    ActivenessStatusFilterType,
    LivenessStatusFilterType,
    ModelReplicaFilterOptions,
    ReadinessStatusFilterType,
)
from ai.backend.manager.repositories.deployment.types.types import (
    LivenessStatusFilter as RepoLivenessStatusFilter,
)
from ai.backend.manager.repositories.deployment.types.types import (
    ReadinessStatusFilter as RepoReadinessStatusFilter,
)
from ai.backend.manager.services.deployment.actions.get_replica_by_id import GetReplicaByIdAction
from ai.backend.manager.services.deployment.actions.model_revision.get_revision_by_id import (
    GetRevisionByIdAction,
)
from ai.backend.manager.services.deployment.actions.search_replicas import SearchReplicasAction

from .model_revision import (
    ModelRevision,
)

ReadinessStatus = strawberry.enum(
    CommonReadinessStatus,
    name="ReadinessStatus",
    description="Added in 25.16.0. This enum represents the readiness status of a replica, indicating whether the deployment has been checked and its health state.",
)

LivenessStatus = strawberry.enum(
    CommonLivenessStatus,
    name="LivenessStatus",
    description="Added in 25.16.0. This enum represents the liveness status of a replica, indicating whether the deployment is currently running and able to serve requests.",
)

ActivenessStatus = strawberry.enum(
    CommonActivenessStatus,
    name="ActivenessStatus",
    description="Added in 25.16.0. This enum represents the activeness status of a replica, indicating whether the deployment is currently active and able to serve requests.",
)


@strawberry.input(description="Added in 25.16.0")
class ReadinessStatusFilter:
    in_: Optional[list[ReadinessStatus]] = strawberry.field(name="in", default=None)
    equals: Optional[ReadinessStatus] = None


@strawberry.input(description="Added in 25.16.0")
class LivenessStatusFilter:
    in_: Optional[list[LivenessStatus]] = strawberry.field(name="in", default=None)
    equals: Optional[LivenessStatus] = None


@strawberry.input(description="Added in 25.16.0")
class ActivenessStatusFilter:
    in_: Optional[list[ActivenessStatus]] = strawberry.field(name="in", default=None)
    equals: Optional[ActivenessStatus] = None


@strawberry.input(description="Added in 25.16.0")
class ReplicaFilter(GQLFilter):
    readiness_status: Optional[ReadinessStatusFilter] = None
    liveness_status: Optional[LivenessStatusFilter] = None
    activeness_status: Optional[ActivenessStatusFilter] = None
    id: Optional[ID] = None
    ids_in: strawberry.Private[Optional[Sequence[UUID]]] = None

    AND: Optional[list["ReplicaFilter"]] = None
    OR: Optional[list["ReplicaFilter"]] = None
    NOT: Optional[list["ReplicaFilter"]] = None

    @override
    def build_conditions(self) -> list[QueryCondition]:
        """Build query conditions from this filter.

        Returns a list of QueryCondition callables that can be applied to SQLAlchemy queries.
        Note: Status filters (readiness/liveness/activeness) are not yet implemented
        at the repository level.
        """
        field_conditions: list[QueryCondition] = []

        # Apply ID filter
        if self.id:
            field_conditions.append(RouteConditions.by_ids([UUID(self.id)]))

        # Apply ids_in filter
        if self.ids_in:
            field_conditions.append(RouteConditions.by_ids(list(self.ids_in)))

        # TODO: Implement status filters at the repository level
        # Status filters (readiness_status, liveness_status, activeness_status) are not yet
        # implemented as RouteConditions. They would require adding new condition factories
        # for filtering by these status fields.

        return field_conditions

    def to_repo_filter(self) -> ModelReplicaFilterOptions:
        repo_filter = ModelReplicaFilterOptions()

        if self.readiness_status:
            if self.readiness_status.in_:
                repo_filter.readiness_status_filter = RepoReadinessStatusFilter(
                    type=ReadinessStatusFilterType.IN,
                    values=[ReadinessStatus(status) for status in self.readiness_status.in_],
                )
            elif self.readiness_status.equals:
                repo_filter.readiness_status_filter = RepoReadinessStatusFilter(
                    type=ReadinessStatusFilterType.EQUALS,
                    values=[ReadinessStatus(self.readiness_status.equals)],
                )
        if self.liveness_status:
            if self.liveness_status.in_:
                repo_filter.liveness_status_filter = RepoLivenessStatusFilter(
                    type=LivenessStatusFilterType.IN,
                    values=[LivenessStatus(status) for status in self.liveness_status.in_],
                )
            elif self.liveness_status.equals:
                repo_filter.liveness_status_filter = RepoLivenessStatusFilter(
                    type=LivenessStatusFilterType.EQUALS,
                    values=[LivenessStatus(self.liveness_status.equals)],
                )
        if self.activeness_status:
            if self.activeness_status.in_:
                repo_filter.activeness_status_filter = RepoActivenessStatus(
                    type=ActivenessStatusFilterType.IN,
                    values=[ActivenessStatus(status) for status in self.activeness_status.in_],
                )
            elif self.activeness_status.equals:
                repo_filter.activeness_status_filter = RepoActivenessStatus(
                    type=ActivenessStatusFilterType.EQUALS,
                    values=[ActivenessStatus(self.activeness_status.equals)],
                )

        if self.id:
            repo_filter.id = UUID(self.id)
        if self.ids_in:
            repo_filter.ids_in = list(self.ids_in)

        # Handle logical operations
        if self.AND:
            repo_filter.AND = [f.to_repo_filter() for f in self.AND]
        if self.OR:
            repo_filter.OR = [f.to_repo_filter() for f in self.OR]
        if self.NOT:
            repo_filter.NOT = [f.to_repo_filter() for f in self.NOT]

        return repo_filter


@strawberry.input(description="Added in 25.16.0")
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


@lru_cache(maxsize=1)
def _get_replica_pagination_spec() -> PaginationSpec:
    """Get pagination specification for replicas.

    Returns a cached PaginationSpec with:
    - Forward pagination: created_at DESC (newest first)
    - Backward pagination: created_at ASC
    """
    return PaginationSpec(
        forward_order=RouteOrders.created_at(ascending=False),
        backward_order=RouteOrders.created_at(ascending=True),
        forward_condition_factory=RouteConditions.by_cursor_forward,
        backward_condition_factory=RouteConditions.by_cursor_backward,
    )


@strawberry.type(description="Added in 25.16.0")
class ModelReplica(Node):
    id: NodeID
    _session_id: strawberry.Private[UUID]
    _revision_id: strawberry.Private[UUID]
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

    @strawberry.field(
        description="The session ID associated with the replica. This can be null right after replica creation."
    )
    async def session(self, info: Info[StrawberryGQLContext]) -> "Session":
        session_global_id = to_global_id(
            ComputeSessionNode, self._session_id, is_target_graphene_object=True
        )
        return Session(id=ID(session_global_id))

    @strawberry.field
    async def revision(self, info: Info[StrawberryGQLContext]) -> ModelRevision:
        """Resolve revision by ID."""
        processor = info.context.processors.deployment
        if processor is None:
            raise ModelDeploymentUnavailable(
                "Model Deployment feature is unavailable. Please contact support."
            )
        result = await processor.get_revision_by_id.wait_for_complete(
            GetRevisionByIdAction(revision_id=self._revision_id)
        )
        return ModelRevision.from_dataclass(result.data)

    @classmethod
    def from_dataclass(cls, data: ModelReplicaData) -> "ModelReplica":
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


@strawberry.type(description="Added in 25.16.0")
class ModelReplicaConnection(Connection[ModelReplica]):
    count: int

    def __init__(self, *args, count: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.count = count

    @classmethod
    def from_dataclass(cls, replicas_data: list[ModelReplicaData]) -> "ModelReplicaConnection":
        nodes = [ModelReplica.from_dataclass(data) for data in replicas_data]
        edges = [ModelReplicaEdge(node=node, cursor=str(node.id)) for node in nodes]

        page_info = PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        )

        return cls(count=len(nodes), edges=edges, page_info=page_info)


@strawberry.type(description="Added in 25.16.0")
class ReplicaStatusChangedPayload:
    replica: ModelReplica


@strawberry.field(description="Added in 25.16.0")
async def replica(id: ID, info: Info[StrawberryGQLContext]) -> Optional[ModelReplica]:
    """Get a specific replica by ID."""
    _, replica_id = resolve_global_id(id)
    processor = info.context.processors.deployment
    if processor is None:
        raise ModelDeploymentUnavailable(
            "Model Deployment feature is unavailable. Please contact support."
        )

    result = await processor.get_replica_by_id.wait_for_complete(
        GetReplicaByIdAction(replica_id=UUID(replica_id))
    )
    if result.data is None:
        return None
    return ModelReplica.from_dataclass(result.data)


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
    processor = info.context.processors.deployment
    if processor is None:
        raise ModelDeploymentUnavailable(
            "Model Deployment feature is unavailable. Please contact support."
        )

    # Build querier using gql_adapter
    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        _get_replica_pagination_spec(),
        filter=filter,
        order_by=order_by,
    )

    action_result = await processor.search_replicas.wait_for_complete(
        SearchReplicasAction(querier=querier)
    )

    nodes = [ModelReplica.from_dataclass(data) for data in action_result.data]
    edges = [ModelReplicaEdge(node=node, cursor=str(node.id)) for node in nodes]

    return ModelReplicaConnection(
        count=action_result.total_count,
        edges=edges,
        page_info=PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
    )


@strawberry.field(description="Added in 25.16.0")
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


@strawberry.subscription(description="Added in 25.16.0")
async def replica_status_changed(
    revision_id: ID,
) -> AsyncGenerator[ReplicaStatusChangedPayload, None]:
    """Subscribe to replica status changes."""
    if False:  # Replace with actual subscription logic
        yield ReplicaStatusChangedPayload(replica=replica)
