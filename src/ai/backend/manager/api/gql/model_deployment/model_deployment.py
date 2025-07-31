import base64
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
    CreateModelRevisionInput,
    ModelRevision,
    ModelRevisionConnection,
    ModelRevisionEdge,
    mock_model_revision_1,
    mock_model_revision_2,
    mock_model_revision_3,
)


@strawberry.enum
class ClusterMode(StrEnum):
    SINGLE_NODE = "SINGLE_NODE"
    MULTI_NODE = "MULTI_NODE"


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
class ClusterConfig:
    mode: ClusterMode
    size: int


@strawberry.type
class ReplicaState:
    desired_replica_count: int
    replicas: ModelReplicaConnection


@strawberry.type
class ScalingRule:
    auto_scaling_rules: list[AutoScalingRule]


@strawberry.type
class ModelDeploymentMetadata:
    name: str
    status: DeploymentStatus
    tags: list[str]
    created_at: datetime
    updated_at: datetime


@strawberry.type
class ModelDeploymentNetworkAccess:
    endpoint_url: Optional[str] = None
    preferred_domain_name: Optional[str] = None
    open_to_public: bool = False
    access_tokens: list[AccessToken]


@strawberry.type
class ResourceConfig:
    resource_group: ResourceGroup
    resource_slots: JSONString
    resource_opts: Optional[JSONString] = None


# Main ModelDeployment Type
@strawberry.type
class ModelDeployment(Node):
    id: NodeID
    metadata: ModelDeploymentMetadata
    network_access: ModelDeploymentNetworkAccess

    revision: Optional[ModelRevision] = None
    revision_history: ModelRevisionConnection

    scaling_rule: ScalingRule
    replica_state: ReplicaState

    deployment_strategy: DeploymentStrategy

    cluster_config: ClusterConfig
    resource_config: ResourceConfig
    created_user: User


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
class ClusterConfigInput:
    mode: ClusterMode
    size: int


@strawberry.input
class ResourceGroupInput:
    name: str


@strawberry.input
class ResourceConfigInput:
    resource_group: ResourceGroupInput
    resource_slots: JSONString
    resource_opts: Optional[JSONString] = None


@strawberry.input
class ModelDeploymentMetadataInput:
    name: str
    tags: Optional[list[str]] = None


@strawberry.input
class ModelDeploymentNetworkAccessInput:
    preferred_domain_name: Optional[str] = None
    open_to_public: bool = False


@strawberry.input
class DeploymentStrategyInput:
    type: DeploymentStrategyType


@strawberry.input
class CreateModelDeploymentInput:
    metadata: ModelDeploymentMetadataInput
    network_access: ModelDeploymentNetworkAccessInput
    cluster_config: ClusterConfigInput
    resource_config: ResourceConfigInput
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


def _generate_mock_global_id() -> str:
    return base64.b64encode(f"default:{uuid4()}".encode("utf-8")).decode()


# Mock Model Replicas
mock_model_replica_1 = ModelReplica(
    id=_generate_mock_global_id(),
    name="llama-3-8b-instruct-replica-01",
    status=ReplicaStatus.HEALTHY,
    revision=mock_model_revision_1,
    routings=[
        RoutingNode(
            id=ID(_generate_mock_global_id()),
            routing_id=uuid4(),
            endpoint="https://api.backend.ai/models/dep-001/routing/01",
            session=uuid4(),
            status="ACTIVE",
            traffic_ratio=0.33,
            created_at=datetime.now() - timedelta(days=5),
            live_stat=cast(
                JSONString, '{"requests": 1523, "latency_ms": 187, "tokens_per_second": 42.5}'
            ),
        )
    ],
)

mock_model_replica_2 = ModelReplica(
    id=_generate_mock_global_id(),
    name="llama-3-8b-instruct-replica-02",
    status=ReplicaStatus.HEALTHY,
    revision=mock_model_revision_1,
    routings=[
        RoutingNode(
            id=ID(_generate_mock_global_id()),
            routing_id=uuid4(),
            endpoint="https://api.backend.ai/models/dep-001/routing/02",
            session=uuid4(),
            status="ACTIVE",
            traffic_ratio=0.33,
            created_at=datetime.now() - timedelta(days=5),
            live_stat=cast(
                JSONString, '{"requests": 1456, "latency_ms": 195, "tokens_per_second": 41.2}'
            ),
        )
    ],
)

mock_model_replica_3 = ModelReplica(
    id=_generate_mock_global_id(),
    name="llama-3-8b-instruct-replica-03",
    status=ReplicaStatus.UNHEALTHY,
    revision=mock_model_revision_1,
    routings=[
        RoutingNode(
            id=ID(_generate_mock_global_id()),
            routing_id=uuid4(),
            endpoint="https://api.backend.ai/models/dep-001/routing/03",
            session=uuid4(),
            status="INACTIVE",
            traffic_ratio=0.0,
            created_at=datetime.now() - timedelta(days=2),
            live_stat=cast(JSONString, '{"requests": 0, "latency_ms": 0, "tokens_per_second": 0}'),
        )
    ],
)

ModelReplicaEdge = Edge[ModelReplica]

# TODO: After implementing the actual logic, remove these mock objects
# Mock Model Deployments
mock_model_deployment_1 = ModelDeployment(
    id=_generate_mock_global_id(),
    metadata=ModelDeploymentMetadata(
        name="Llama 3.8B Instruct",
        status=DeploymentStatus.ACTIVE,
        tags=["production", "llm", "chat", "instruct"],
        created_at=datetime.now() - timedelta(days=30),
        updated_at=datetime.now() - timedelta(hours=2),
    ),
    network_access=ModelDeploymentNetworkAccess(
        endpoint_url="https://api.backend.ai/models/dep-001",
        preferred_domain_name="llama-3-8b.models.backend.ai",
        open_to_public=True,
        access_tokens=[],
    ),
    cluster_config=ClusterConfig(mode=ClusterMode.SINGLE_NODE, size=1),
    resource_config=ResourceConfig(
        resource_group=ResourceGroup(id=ID(_generate_mock_global_id())),
        resource_slots=cast(
            JSONString,
            '{"cpu": 8, "mem": "32G", "cuda.shares": 1, "cuda.device": 1}',
        ),
        resource_opts=cast(
            JSONString,
            '{"shmem": "2G", "reserved_time": "24h", "scaling_group": "us-east-1"}',
        ),
    ),
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
    scaling_rule=ScalingRule(
        auto_scaling_rules=[
            AutoScalingRule(id=ID(_generate_mock_global_id())),
            AutoScalingRule(id=ID(_generate_mock_global_id())),
        ]
    ),
    replica_state=ReplicaState(
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
    created_user=User(id=ID(_generate_mock_global_id())),
)

mock_model_deployment_2 = ModelDeployment(
    id=_generate_mock_global_id(),
    metadata=ModelDeploymentMetadata(
        name="Mistral 7B v0.3",
        status=DeploymentStatus.ACTIVE,
        tags=["staging", "llm", "experimental"],
        created_at=datetime.now() - timedelta(days=20),
        updated_at=datetime.now() - timedelta(days=1),
    ),
    network_access=ModelDeploymentNetworkAccess(
        endpoint_url="https://api.backend.ai/models/dep-002",
        preferred_domain_name="mistral-7b.models.backend.ai",
        open_to_public=False,
        access_tokens=[],
    ),
    cluster_config=ClusterConfig(mode=ClusterMode.SINGLE_NODE, size=1),
    resource_config=ResourceConfig(
        resource_group=ResourceGroup(id=ID(_generate_mock_global_id())),
        resource_slots=cast(
            JSONString,
            '{"cpu": 8, "mem": "32G", "cuda.shares": 1, "cuda.device": 1}',
        ),
        resource_opts=cast(
            JSONString,
            '{"shmem": "2G", "reserved_time": "24h", "scaling_group": "us-east-1"}',
        ),
    ),
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
    scaling_rule=ScalingRule(auto_scaling_rules=[]),
    replica_state=ReplicaState(
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
    created_user=User(id=ID(_generate_mock_global_id())),
)

mock_model_deployment_3 = ModelDeployment(
    id=_generate_mock_global_id(),
    metadata=ModelDeploymentMetadata(
        name="Gemma 2.9B",
        status=DeploymentStatus.INACTIVE,
        tags=["development", "llm", "testing"],
        created_at=datetime.now() - timedelta(days=15),
        updated_at=datetime.now() - timedelta(days=7),
    ),
    network_access=ModelDeploymentNetworkAccess(
        endpoint_url=None,
        preferred_domain_name=None,
        open_to_public=False,
        access_tokens=[],
    ),
    cluster_config=ClusterConfig(mode=ClusterMode.SINGLE_NODE, size=1),
    resource_config=ResourceConfig(
        resource_group=ResourceGroup(id=ID(_generate_mock_global_id())),
        resource_slots=cast(
            JSONString,
            '{"cpu": 8, "mem": "32G", "cuda.shares": 1, "cuda.device": 1}',
        ),
        resource_opts=cast(
            JSONString,
            '{"shmem": "2G", "reserved_time": "24h", "scaling_group": "us-east-1"}',
        ),
    ),
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
    scaling_rule=ScalingRule(auto_scaling_rules=[]),
    replica_state=ReplicaState(
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
    created_user=User(id=ID(_generate_mock_global_id())),
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
