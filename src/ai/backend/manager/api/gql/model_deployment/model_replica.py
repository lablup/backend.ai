from collections.abc import Sequence
from datetime import datetime
from typing import AsyncGenerator, Optional
from uuid import UUID

import strawberry
from aiotools import apartial
from strawberry import ID, Info
from strawberry.dataloader import DataLoader
from strawberry.relay import Connection, Edge, Node, NodeID, PageInfo

from ai.backend.common.data.model_deployment.types import ActivenessStatus as CommonActivenessStatus
from ai.backend.common.data.model_deployment.types import LivenessStatus as CommonLivenessStatus
from ai.backend.common.data.model_deployment.types import ReadinessStatus as CommonReadinessStatus
from ai.backend.common.exception import ModelDeploymentUnavailable
from ai.backend.manager.api.gql.base import (
    JSONString,
    OrderDirection,
    build_page_info,
    build_pagination_options,
    resolve_global_id,
    to_global_id,
)
from ai.backend.manager.api.gql.session import Session
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.data.deployment.types import ModelReplicaData, ReplicaOrderField
from ai.backend.manager.models.gql_models.session import ComputeSessionNode
from ai.backend.manager.repositories.deployment.types.types import (
    ActivenessStatusFilter as RepoActivenessStatus,
)
from ai.backend.manager.repositories.deployment.types.types import (
    ActivenessStatusFilterType,
    LivenessStatusFilterType,
    ModelReplicaFilterOptions,
    ModelReplicaOrderingOptions,
    ReadinessStatusFilterType,
)
from ai.backend.manager.repositories.deployment.types.types import (
    LivenessStatusFilter as RepoLivenessStatusFilter,
)
from ai.backend.manager.repositories.deployment.types.types import (
    ReadinessStatusFilter as RepoReadinessStatusFilter,
)
from ai.backend.manager.services.deployment.actions.batch_load_replicas_by_deployment_ids import (
    BatchLoadReplicasByDeploymentIdsAction,
)
from ai.backend.manager.services.deployment.actions.batch_load_replicas_by_revision_ids import (
    BatchLoadReplicasByRevisionIdsAction,
)
from ai.backend.manager.services.deployment.actions.list_replicas import ListReplicasAction
from ai.backend.manager.types import PaginationOptions

from .model_revision import (
    ModelRevision,
)

ReadinessStatus = strawberry.enum(
    CommonReadinessStatus,
    name="ReadinessStatus",
    description="Added in 25.15.0. This enum represents the readiness status of a replica, indicating whether the deployment has been checked and its health state.",
)

LivenessStatus = strawberry.enum(
    CommonLivenessStatus,
    name="LivenessStatus",
    description="Added in 25.15.0. This enum represents the liveness status of a replica, indicating whether the deployment is currently running and able to serve requests.",
)

ActivenessStatus = strawberry.enum(
    CommonActivenessStatus,
    name="ActivenessStatus",
    description="Added in 25.15.0. This enum represents the activeness status of a replica, indicating whether the deployment is currently active and able to serve requests.",
)


@strawberry.input(description="Added in 25.15.0")
class ReadinessStatusFilter:
    in_: Optional[list[ReadinessStatus]] = strawberry.field(name="in", default=None)
    equals: Optional[ReadinessStatus] = None


@strawberry.input(description="Added in 25.15.0")
class LivenessStatusFilter:
    in_: Optional[list[LivenessStatus]] = strawberry.field(name="in", default=None)
    equals: Optional[LivenessStatus] = None


@strawberry.input(description="Added in 25.15.0")
class ActivenessStatusFilter:
    in_: Optional[list[ActivenessStatus]] = strawberry.field(name="in", default=None)
    equals: Optional[ActivenessStatus] = None


@strawberry.input(description="Added in 25.15.0")
class ReplicaFilter:
    readiness_status: Optional[ReadinessStatusFilter] = None
    liveness_status: Optional[LivenessStatusFilter] = None
    activeness_status: Optional[ActivenessStatusFilter] = None
    id: Optional[ID] = None

    AND: Optional[list["ReplicaFilter"]] = None
    OR: Optional[list["ReplicaFilter"]] = None
    NOT: Optional[list["ReplicaFilter"]] = None

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

        # Handle logical operations
        if self.AND:
            repo_filter.AND = [f.to_repo_filter() for f in self.AND]
        if self.OR:
            repo_filter.OR = [f.to_repo_filter() for f in self.OR]
        if self.NOT:
            repo_filter.NOT = [f.to_repo_filter() for f in self.NOT]

        return repo_filter


@strawberry.input(description="Added in 25.15.0")
class ReplicaOrderBy:
    field: ReplicaOrderField
    direction: OrderDirection = OrderDirection.DESC


@strawberry.type(description="Added in 25.15.0")
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
        """Resolve revision using dataloader."""
        revision_loader = DataLoader(apartial(ModelRevision.batch_load_by_ids, info.context))
        revision: list[ModelRevision] = await revision_loader.load(self._revision_id)
        return revision[0]

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

    @classmethod
    async def batch_load_by_deployment_ids(
        cls, ctx: StrawberryGQLContext, deployment_ids: Sequence[UUID]
    ) -> list["ModelReplica"]:
        """Batch load replicas by their IDs."""
        processor = ctx.processors.deployment
        if processor is None:
            raise ModelDeploymentUnavailable(
                "Model Deployment feature is unavailable. Please contact support."
            )

        action_result = await processor.batch_load_replicas_by_deployment_ids.wait_for_complete(
            BatchLoadReplicasByDeploymentIdsAction(deployment_ids=list(deployment_ids))
        )

        replicas_map = action_result.data
        replicas = []
        for deployment_id in deployment_ids:
            if deployment_id in replicas_map:
                replicas.extend(replicas_map[deployment_id])
        return [cls.from_dataclass(data) for data in replicas]

    @classmethod
    async def batch_load_by_revision_ids(
        cls, ctx: StrawberryGQLContext, revision_ids: Sequence[UUID]
    ) -> list["ModelReplica"]:
        """Batch load replicas by their revision IDs."""
        processor = ctx.processors.deployment
        if processor is None:
            raise ModelDeploymentUnavailable(
                "Model Deployment feature is unavailable. Please contact support."
            )

        replicas = []
        action_results = await processor.batch_load_replicas_by_revision_ids.wait_for_complete(
            BatchLoadReplicasByRevisionIdsAction(revision_ids=list(revision_ids))
        )
        replicas_map = action_results.data
        for revision_id in revision_ids:
            if revision_id in replicas_map:
                replicas.extend(replicas_map[revision_id])

        return [cls.from_dataclass(data) for data in replicas]


ModelReplicaEdge = Edge[ModelReplica]


@strawberry.type(description="Added in 25.15.0")
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


@strawberry.type(description="Added in 25.15.0")
class ReplicaStatusChangedPayload:
    replica: ModelReplica


@strawberry.field(description="Added in 25.15.0")
async def replica(id: ID, info: Info[StrawberryGQLContext]) -> Optional[ModelReplica]:
    """Get a specific replica by ID."""
    _, replica_id = resolve_global_id(id)
    replica_loader = DataLoader(apartial(ModelReplica.batch_load_by_revision_ids, info.context))
    replicas: list[ModelReplica] = await replica_loader.load(UUID(replica_id))
    return replicas[0]


def _convert_gql_replica_ordering_to_repo_ordering(
    order_by: Optional[list[ReplicaOrderBy]],
) -> ModelReplicaOrderingOptions:
    if not order_by:
        return ModelReplicaOrderingOptions()

    repo_order_by = []
    for order in order_by:
        desc = order.direction == OrderDirection.DESC
        repo_order_by.append((order.field, desc))

    return ModelReplicaOrderingOptions(order_by=repo_order_by)


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
    repo_filter = None
    if filter:
        repo_filter = filter.to_repo_filter()

    repo_ordering = _convert_gql_replica_ordering_to_repo_ordering(order_by)

    pagination_options = build_pagination_options(
        before=before,
        after=after,
        first=first,
        last=last,
        limit=limit,
        offset=offset,
    )

    processor = info.context.processors.deployment
    if processor is None:
        raise ModelDeploymentUnavailable(
            "Model Deployment feature is unavailable. Please contact support."
        )

    action_result = await processor.list_replicas.wait_for_complete(
        ListReplicasAction(
            pagination=PaginationOptions(),
            ordering=repo_ordering,
            filters=repo_filter,
        )
    )
    edges = []
    for replica_data in action_result.data:
        node = ModelReplica.from_dataclass(replica_data)
        edge = ModelReplicaEdge(node=node, cursor=str(node.id))
        edges.append(edge)

    page_info = build_page_info(
        edges=edges, total_count=action_result.total_count, pagination_options=pagination_options
    )

    return ModelReplicaConnection(
        count=action_result.total_count,
        edges=edges,
        page_info=page_info.to_strawberry_page_info(),
    )


@strawberry.field(description="Added in 25.15.0")
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


@strawberry.subscription(description="Added in 25.15.0")
async def replica_status_changed(
    revision_id: ID,
) -> AsyncGenerator[ReplicaStatusChangedPayload, None]:
    """Subscribe to replica status changes."""
    if False:  # Replace with actual subscription logic
        yield ReplicaStatusChangedPayload(replica=replica)
