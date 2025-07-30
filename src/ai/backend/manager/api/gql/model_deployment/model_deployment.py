from datetime import datetime, timedelta
from enum import StrEnum
from typing import AsyncGenerator, Optional, cast
from uuid import uuid4

import strawberry
from strawberry import ID, Info, relay
from strawberry.relay import Connection, Edge, Node, NodeID, PageInfo
from strawberry.relay.types import NodeIterableType

from ai.backend.manager.api.gql.base import JSONString, OrderDirection, StringFilter
from ai.backend.manager.api.gql.federated_types import (
    AccessToken,
    AutoScalingRule,
    ResourceGroup,
    User,
)
from ai.backend.manager.api.gql.model_deployment.routing import (
    RoutingNode,
)

from .model_revision import (
    ClusterConfigInput,
    CreateModelRevisionInput,
    ModelRevision,
    ModelRevisionConnection,
    ModelRevisionEdge,
    mock_model_revision_1,
    mock_model_revision_2,
    mock_model_revision_3,
)


@strawberry.enum
class DeploymentStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


@strawberry.enum
class ReplicaStatus(StrEnum):
    HEALTHY = "HEALTHY"
    UNHEALTHY = "UNHEALTHY"


@strawberry.enum
class DeploymentStrategyType(StrEnum):
    ROLLING = "ROLLING"
    BLUE_GREEN = "BLUE_GREEN"
    CANARY = "CANARY"


@strawberry.enum
class DeploymentOrderField(StrEnum):
    CREATED_AT = "CREATED_AT"
    UPDATED_AT = "UPDATED_AT"
    NAME = "NAME"


@strawberry.type
class DeploymentStrategy:
    type: DeploymentStrategyType


@strawberry.type
class ModelReplica(Node):
    id: NodeID
    name: str
    status: ReplicaStatus
    revision: ModelRevision
    routings: list[RoutingNode]


@strawberry.type
class ModelReplicaConnection(Connection[ModelReplica]):
    @strawberry.field
    def count(self) -> int:
        return 0

    @classmethod
    def resolve_connection(
        cls,
        nodes: NodeIterableType[ModelReplica],
        *,
        info: Info,
        before: Optional[str] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        last: Optional[int] = None,
        max_results: Optional[int] = None,
        **kwargs,
    ) -> "ModelReplicaConnection":
        return cls(
            edges=[],
            page_info=relay.PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor=None,
                end_cursor=None,
            ),
        )


@strawberry.type
class ReplicaManagement:
    desired_replica_count: int
    replicas: ModelReplicaConnection


@strawberry.type
class Scale:
    auto_scaling_rules: list[AutoScalingRule]


# Main ModelDeployment Type
@strawberry.type
class ModelDeployment(Node):
    id: NodeID
    name: str
    endpoint_url: Optional[str] = None
    preferred_domain_name: Optional[str] = None
    status: DeploymentStatus
    open_to_public: bool
    tags: list[str]

    revision: Optional[ModelRevision] = None
    revision_history: ModelRevisionConnection

    scale: Scale
    replica_management: ReplicaManagement

    deployment_strategy: DeploymentStrategy

    # Federated types from existing schema
    created_user: User
    resource_group: ResourceGroup
    access_tokens: list[AccessToken]

    created_at: datetime
    updated_at: datetime


# Filter Types
@strawberry.input
class DeploymentFilter:
    status: Optional[DeploymentStatus] = None
    open_to_public: Optional[bool] = None
    tags: Optional[list[StringFilter]] = None

    AND: Optional["DeploymentFilter"] = None
    OR: Optional["DeploymentFilter"] = None
    NOT: Optional["DeploymentFilter"] = None
    DISTINCT: Optional[bool] = None


@strawberry.input
class DeploymentOrderBy:
    field: DeploymentOrderField
    direction: OrderDirection = OrderDirection.DESC


# Payload Types
@strawberry.type
class CreateModelDeploymentPayload:
    deployment: ModelDeployment


@strawberry.type
class UpdateModelDeploymentPayload:
    deployment: Optional[ModelDeployment] = None


@strawberry.type
class DeleteModelDeploymentPayload:
    deployment: Optional[ModelDeployment] = None


@strawberry.type
class DeploymentStatusChangedPayload:
    deployment: ModelDeployment


@strawberry.type
class ReplicaStatusChangedPayload:
    replica: ModelReplica


# Input Types
@strawberry.input
class RollingConfigInput:
    max_surge: int
    max_unavailable: int


@strawberry.input
class BlueGreenConfigInput:
    auto_promotion_enabled: bool
    termination_wait_time: int


@strawberry.input
class CanaryConfigInput:
    canary_percentage: int
    canary_duration: str
    success_threshold: float


@strawberry.input
class DeploymentStrategyInput:
    type: DeploymentStrategyType


@strawberry.input
class CreateModelDeploymentInput:
    name: str
    preferred_domain_name: Optional[str] = None
    open_to_public: bool
    tags: Optional[list[str]] = None
    cluster_config: ClusterConfigInput
    deployment_strategy: DeploymentStrategyInput
    initial_revision: CreateModelRevisionInput


@strawberry.input
class UpdateModelDeploymentInput:
    id: ID
    open_to_public: Optional[bool] = None
    tags: Optional[list[str]] = None
    deployment_strategy: Optional[DeploymentStrategyInput] = None
    active_revision_id: Optional[ID] = None


@strawberry.input
class DeleteModelDeploymentInput:
    id: ID


# Mock Model Replicas
mock_model_replica_1 = ModelReplica(
    id="replica-001",
    name="llama-3-8b-instruct-replica-01",
    status=ReplicaStatus.HEALTHY,
    revision=mock_model_revision_1,
    routings=[
        RoutingNode(
            id=ID("routing-001"),
            routing_id=uuid4(),
            endpoint="https://api.backend.ai/models/dep-001/routing/01",
            session=uuid4(),
            status="ACTIVE",
            traffic_ratio=0.33,
            created_at=datetime.now() - timedelta(days=5),
            error_data=cast(JSONString, '{"error": null}'),
            live_stat=cast(
                JSONString, '{"requests": 1523, "latency_ms": 187, "tokens_per_second": 42.5}'
            ),
        )
    ],
)

mock_model_replica_2 = ModelReplica(
    id="replica-002",
    name="llama-3-8b-instruct-replica-02",
    status=ReplicaStatus.HEALTHY,
    revision=mock_model_revision_1,
    routings=[
        RoutingNode(
            id=ID("routing-002"),
            routing_id=uuid4(),
            endpoint="https://api.backend.ai/models/dep-001/routing/02",
            session=uuid4(),
            status="ACTIVE",
            traffic_ratio=0.33,
            created_at=datetime.now() - timedelta(days=5),
            error_data=cast(JSONString, '{"error": null}'),
            live_stat=cast(
                JSONString, '{"requests": 1456, "latency_ms": 195, "tokens_per_second": 41.2}'
            ),
        )
    ],
)

mock_model_replica_3 = ModelReplica(
    id="replica-003",
    name="llama-3-8b-instruct-replica-03",
    status=ReplicaStatus.UNHEALTHY,
    revision=mock_model_revision_1,
    routings=[
        RoutingNode(
            id=ID("routing-003"),
            routing_id=uuid4(),
            endpoint="https://api.backend.ai/models/dep-001/routing/03",
            session=uuid4(),
            status="INACTIVE",
            traffic_ratio=0.0,
            created_at=datetime.now() - timedelta(days=2),
            error_data=cast(
                JSONString, '{"error": "OOMKilled", "message": "Container exceeded memory limit"}'
            ),
            live_stat=cast(JSONString, '{"requests": 0, "latency_ms": 0, "tokens_per_second": 0}'),
        )
    ],
)

ModelReplicaEdge = Edge[ModelReplica]

# TODO: After implementing the actual logic, remove these mock objects
# Mock Model Deployments
mock_model_deployment_1 = ModelDeployment(
    id="dep-001",
    name="llama-3-8b-instruct",
    endpoint_url="https://api.backend.ai/models/dep-001",
    preferred_domain_name="llama-3-8b.models.backend.ai",
    status=DeploymentStatus.ACTIVE,
    open_to_public=True,
    tags=["production", "llm", "chat", "instruct"],
    revision=mock_model_revision_1,
    revision_history=ModelRevisionConnection(
        edges=[
            ModelRevisionEdge(node=mock_model_revision_1, cursor="rev-cursor-1"),
            ModelRevisionEdge(node=mock_model_revision_2, cursor="rev-cursor-2"),
        ],
        page_info=PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor="rev-cursor-1",
            end_cursor="rev-cursor-2",
        ),
    ),
    scale=Scale(
        auto_scaling_rules=[
            AutoScalingRule(id=ID("asr-cpu-001")),
            AutoScalingRule(id=ID("asr-gpu-001")),
        ]
    ),
    replica_management=ReplicaManagement(
        desired_replica_count=3,
        replicas=ModelReplicaConnection(
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
        ),
    ),
    deployment_strategy=DeploymentStrategy(type=DeploymentStrategyType.ROLLING),
    created_user=User(id=ID("user-001")),
    resource_group=ResourceGroup(id=ID("rg-us-east-1")),
    access_tokens=[],
    created_at=datetime.now() - timedelta(days=30),
    updated_at=datetime.now() - timedelta(hours=2),
)

mock_model_deployment_2 = ModelDeployment(
    id="dep-002",
    name="mistral-7b-v0.3",
    endpoint_url="https://api.backend.ai/models/dep-002",
    preferred_domain_name="mistral-7b.models.backend.ai",
    status=DeploymentStatus.ACTIVE,
    open_to_public=False,
    tags=["staging", "llm", "experimental"],
    revision=mock_model_revision_3,
    revision_history=ModelRevisionConnection(
        edges=[
            ModelRevisionEdge(node=mock_model_revision_3, cursor="rev-cursor-3"),
        ],
        page_info=PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor="rev-cursor-3",
            end_cursor="rev-cursor-3",
        ),
    ),
    scale=Scale(auto_scaling_rules=[]),
    replica_management=ReplicaManagement(
        desired_replica_count=1,
        replicas=ModelReplicaConnection(
            edges=[
                ModelReplicaEdge(node=mock_model_replica_1, cursor="replica-cursor-1"),
                ModelReplicaEdge(node=mock_model_replica_2, cursor="replica-cursor-2"),
            ],
            page_info=PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor=None,
                end_cursor=None,
            ),
        ),
    ),
    deployment_strategy=DeploymentStrategy(type=DeploymentStrategyType.BLUE_GREEN),
    created_user=User(id=ID("user-002")),
    resource_group=ResourceGroup(id=ID("rg-us-west-2")),
    access_tokens=[],
    created_at=datetime.now() - timedelta(days=20),
    updated_at=datetime.now() - timedelta(days=1),
)

mock_model_deployment_3 = ModelDeployment(
    id="dep-003",
    name="gemma-2-9b",
    endpoint_url=None,
    preferred_domain_name=None,
    status=DeploymentStatus.INACTIVE,
    open_to_public=False,
    tags=["development", "llm", "testing"],
    revision=None,
    revision_history=ModelRevisionConnection(
        edges=[],
        page_info=PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=None,
            end_cursor=None,
        ),
    ),
    scale=Scale(auto_scaling_rules=[]),
    replica_management=ReplicaManagement(
        desired_replica_count=0,
        replicas=ModelReplicaConnection(
            edges=[],
            page_info=PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor=None,
                end_cursor=None,
            ),
        ),
    ),
    deployment_strategy=DeploymentStrategy(type=DeploymentStrategyType.CANARY),
    created_user=User(id=ID("user-003")),
    resource_group=ResourceGroup(id=ID("rg-eu-west-1")),
    access_tokens=[],
    created_at=datetime.now() - timedelta(days=15),
    updated_at=datetime.now() - timedelta(days=7),
)


ModelDeploymentEdge = Edge[ModelDeployment]


# Connection types for Relay support
@strawberry.type
class ModelDeploymentConnection(Connection[ModelDeployment]):
    @strawberry.field
    def count(self) -> int:
        return 0

    @classmethod
    def resolve_connection(
        cls,
        nodes: NodeIterableType[ModelDeployment],
        *,
        info: Info,
        before: Optional[str] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        last: Optional[int] = None,
        max_results: Optional[int] = None,
        **kwargs,
    ) -> "ModelDeploymentConnection":
        mock_deployments = [
            mock_model_deployment_1,
            mock_model_deployment_2,
            mock_model_deployment_3,
        ]
        return cls(
            edges=[
                Edge(node=deployment, cursor=str(i))
                for i, deployment in enumerate(mock_deployments)
            ],
            page_info=relay.PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor=None,
                end_cursor=None,
            ),
        )


# Resolvers
@strawberry.relay.connection(ModelDeploymentConnection)
async def deployments(
    filter: Optional[DeploymentFilter] = None,
    order_by: Optional[DeploymentOrderBy] = None,
    first: Optional[int] = None,
    after: Optional[str] = None,
) -> list[ModelDeployment]:
    """List deployments with optional filtering and pagination."""
    # Return a list of mock deployments with more details
    deployments = [
        mock_model_deployment_1,
        mock_model_deployment_2,
        mock_model_deployment_3,
    ]

    return deployments


@strawberry.field
async def deployment(id: ID) -> Optional[ModelDeployment]:
    """Get a specific deployment by ID."""
    return None


@strawberry.field
async def replica(id: ID) -> Optional[ModelReplica]:
    """Get a specific replica by ID."""

    return ModelReplica(
        id=id,
        name="llama-3-8b-instruct-replica-01",
        status=ReplicaStatus.HEALTHY,
        revision=mock_model_revision_1,
        routings=[],
    )


@strawberry.mutation
async def create_model_deployment(
    input: CreateModelDeploymentInput,
) -> CreateModelDeploymentPayload:
    """Create a new model deployment."""
    # Create a dummy deployment for placeholder
    return CreateModelDeploymentPayload(deployment=mock_model_deployment_1)


@strawberry.mutation
async def update_model_deployment(
    input: UpdateModelDeploymentInput,
) -> UpdateModelDeploymentPayload:
    """Update an existing model deployment."""
    # Create a dummy deployment for placeholder
    return UpdateModelDeploymentPayload(deployment=mock_model_deployment_1)


@strawberry.mutation
async def delete_model_deployment(
    input: DeleteModelDeploymentInput,
) -> DeleteModelDeploymentPayload:
    """Delete a model deployment."""
    return DeleteModelDeploymentPayload(deployment=None)


@strawberry.subscription
async def deployment_status_changed(
    deployment_id: ID,
) -> AsyncGenerator[DeploymentStatusChangedPayload, None]:
    """Subscribe to deployment status changes."""
    deployment = [mock_model_deployment_1, mock_model_deployment_2, mock_model_deployment_3]

    for dep in deployment:
        yield DeploymentStatusChangedPayload(deployment=dep)


@strawberry.subscription
async def replica_status_changed(
    revision_id: ID,
) -> AsyncGenerator[ReplicaStatusChangedPayload, None]:
    """Subscribe to replica status changes."""
    replicas = [mock_model_replica_1, mock_model_replica_2, mock_model_replica_3]

    for replica in replicas:
        yield ReplicaStatusChangedPayload(replica=replica)
