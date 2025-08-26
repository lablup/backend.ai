from datetime import datetime, timedelta
from enum import StrEnum
from typing import AsyncGenerator, Optional, cast
from uuid import UUID, uuid4

import strawberry
from strawberry import ID, Info, relay
from strawberry.relay import Connection, Edge, Node, NodeID, PageInfo
from strawberry.relay.types import NodeIterableType

from ai.backend.manager.api.gql.base import JSONString, OrderDirection, StringFilter
from ai.backend.manager.api.gql.model_deployment.access_token import (
    AccessTokenConnection,
    AccessTokenEdge,
    mock_access_token_1,
    mock_access_token_2,
    mock_access_token_3,
    mock_access_token_4,
    mock_access_token_5,
)
from ai.backend.manager.api.gql.model_deployment.auto_scaling_rule import (
    AutoScalingRule,
    mock_scaling_rule_1,
    mock_scaling_rule_2,
)
from ai.backend.manager.api.gql.model_deployment.routing import (
    RoutingNode,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.user import User

from .model_revision import (
    CreateModelRevisionInput,
    ModelRevision,
    ModelRevisionConnection,
    ModelRevisionEdge,
    mock_model_revision_1,
    mock_model_revision_2,
    mock_model_revision_3,
)


@strawberry.enum(description="Added in 25.13.0")
class DeploymentStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    CREATED = "CREATED"
    DEPLOYING = "DEPLOYING"
    READY = "READY"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"


@strawberry.enum(description="Added in 25.13.0")
class ReplicaStatus(StrEnum):
    HEALTHY = "HEALTHY"
    UNHEALTHY = "UNHEALTHY"


@strawberry.enum(description="Added in 25.13.0")
class DeploymentStrategyType(StrEnum):
    ROLLING = "ROLLING"
    BLUE_GREEN = "BLUE_GREEN"
    CANARY = "CANARY"


@strawberry.enum(description="Added in 25.13.0")
class DeploymentOrderField(StrEnum):
    CREATED_AT = "CREATED_AT"
    UPDATED_AT = "UPDATED_AT"
    NAME = "NAME"


@strawberry.type(description="Added in 25.13.0")
class DeploymentStrategy:
    type: DeploymentStrategyType


@strawberry.type(description="Added in 25.13.0")
class ModelReplica(Node):
    id: NodeID
    name: str
    status: ReplicaStatus
    revision: ModelRevision
    routings: list[RoutingNode]


@strawberry.type(description="Added in 25.13.0")
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


@strawberry.type(description="Added in 25.13.0")
class ReplicaState:
    desired_replica_count: int
    replicas: ModelReplicaConnection


@strawberry.type(description="Added in 25.13.0")
class ScalingRule:
    auto_scaling_rules: list[AutoScalingRule]


@strawberry.type(description="Added in 25.13.0")
class ModelDeploymentMetadata:
    name: str
    status: DeploymentStatus
    tags: list[str]
    created_at: datetime
    updated_at: datetime


@strawberry.type(description="Added in 25.13.0")
class ModelDeploymentNetworkAccess:
    endpoint_url: Optional[str] = None
    preferred_domain_name: Optional[str] = None
    open_to_public: bool = False
    access_tokens: AccessTokenConnection


# Main ModelDeployment Type
@strawberry.type(description="Added in 25.13.0")
class ModelDeployment(Node):
    id: NodeID
    metadata: ModelDeploymentMetadata
    network_access: ModelDeploymentNetworkAccess

    revision: Optional[ModelRevision] = None
    revision_history: ModelRevisionConnection

    scaling_rule: ScalingRule
    replica_state: ReplicaState

    default_deployment_strategy: DeploymentStrategy

    created_user: User


# Filter Types
@strawberry.input(description="Added in 25.13.0")
class DeploymentStatusFilter:
    in_: Optional[list[DeploymentStatus]] = strawberry.field(name="in", default=None)
    equals: Optional[DeploymentStatus] = None


@strawberry.input(description="Added in 25.13.0")
class DeploymentFilter:
    name: Optional[StringFilter] = None
    status: Optional[DeploymentStatusFilter] = None
    open_to_public: Optional[bool] = None
    tags: Optional[StringFilter] = None

    AND: Optional[list["DeploymentFilter"]] = None
    OR: Optional[list["DeploymentFilter"]] = None
    NOT: Optional[list["DeploymentFilter"]] = None
    DISTINCT: Optional[bool] = None


@strawberry.input(description="Added in 25.13.0")
class ReplicaStatusFilter:
    in_: Optional[list[ReplicaStatus]] = strawberry.field(name="in", default=None)
    equals: Optional[ReplicaStatus] = None


@strawberry.input(description="Added in 25.13.0")
class ReplicaFilter:
    status: Optional[ReplicaStatusFilter] = None

    AND: Optional[list["ReplicaFilter"]] = None
    OR: Optional[list["ReplicaFilter"]] = None
    NOT: Optional[list["ReplicaFilter"]] = None
    DISTINCT: Optional[bool] = None


@strawberry.input(description="Added in 25.13.0")
class DeploymentOrderBy:
    field: DeploymentOrderField
    direction: OrderDirection = OrderDirection.DESC


# Payload Types
@strawberry.type(description="Added in 25.13.0")
class CreateModelDeploymentPayload:
    deployment: ModelDeployment


@strawberry.type(description="Added in 25.13.0")
class UpdateModelDeploymentPayload:
    deployment: Optional[ModelDeployment] = None


@strawberry.type(description="Added in 25.13.0")
class DeleteModelDeploymentPayload:
    deployment: Optional[ModelDeployment] = None


@strawberry.type(description="Added in 25.13.0")
class DeploymentStatusChangedPayload:
    deployment: ModelDeployment


@strawberry.type(description="Added in 25.13.0")
class ReplicaStatusChangedPayload:
    replica: ModelReplica


# Input Types
@strawberry.input(description="Added in 25.13.0")
class ModelDeploymentMetadataInput:
    name: str
    tags: Optional[list[str]] = None


@strawberry.input(description="Added in 25.13.0")
class ModelDeploymentNetworkAccessInput:
    preferred_domain_name: Optional[str] = None
    open_to_public: bool = False


@strawberry.input(description="Added in 25.13.0")
class DeploymentStrategyInput:
    type: DeploymentStrategyType


@strawberry.input(description="Added in 25.13.0")
class CreateModelDeploymentInput:
    metadata: ModelDeploymentMetadataInput
    network_access: ModelDeploymentNetworkAccessInput
    default_deployment_strategy: DeploymentStrategyInput
    desired_replica_count: int
    initial_revision: CreateModelRevisionInput


@strawberry.input(description="Added in 25.13.0")
class UpdateModelDeploymentInput:
    id: ID
    open_to_public: Optional[bool] = None
    tags: Optional[list[str]] = None
    default_deployment_strategy: Optional[DeploymentStrategyInput] = None
    active_revision_id: Optional[ID] = None


@strawberry.input(description="Added in 25.13.0")
class DeleteModelDeploymentInput:
    id: ID


# Mock Model Replicas
mock_replica_id_1 = "b62f9890-228a-40c9-a614-63387805b9a7"
mock_routing_id_1 = "60bf21b8-21a9-4655-aaeb-479a4ef02358"
mock_model_replica_1 = ModelReplica(
    id=UUID(mock_replica_id_1),
    name="llama-3-8b-instruct-replica-01",
    status=ReplicaStatus.HEALTHY,
    revision=mock_model_revision_1,
    routings=[
        RoutingNode(
            id=UUID(mock_routing_id_1),
            routing_id=uuid4(),
            endpoint_url="https://api.backend.ai/models/dep-001/routing/01",
            session_id=uuid4(),
            status="ACTIVE",
            traffic_ratio=0.33,
            created_at=datetime.now() - timedelta(days=5),
            live_stat=cast(
                JSONString, '{"requests": 1523, "latency_ms": 187, "tokens_per_second": 42.5}'
            ),
        )
    ],
)

mock_replica_id_2 = "7562e9d4-a368-4e28-9092-65eb91534bac"
mock_routing_id_2 = "21ede864-725d-4933-96f6-6df727f92217"
mock_model_replica_2 = ModelReplica(
    id=UUID(mock_replica_id_2),
    name="llama-3-8b-instruct-replica-02",
    status=ReplicaStatus.HEALTHY,
    revision=mock_model_revision_1,
    routings=[
        RoutingNode(
            id=UUID(mock_routing_id_2),
            routing_id=uuid4(),
            endpoint_url="https://api.backend.ai/models/dep-001/routing/02",
            session_id=uuid4(),
            status="ACTIVE",
            traffic_ratio=0.33,
            created_at=datetime.now() - timedelta(days=5),
            live_stat=cast(
                JSONString, '{"requests": 1456, "latency_ms": 195, "tokens_per_second": 41.2}'
            ),
        )
    ],
)

mock_replica_id_3 = "2a2388ea-a312-422a-b77e-0e0b61c48145"
mock_routing_id_3 = "9613c8d1-53f1-4b8a-9cc4-6333d00afef0"
mock_model_replica_3 = ModelReplica(
    id=UUID(mock_replica_id_3),
    name="llama-3-8b-instruct-replica-03",
    status=ReplicaStatus.UNHEALTHY,
    revision=mock_model_revision_1,
    routings=[
        RoutingNode(
            id=UUID(mock_routing_id_3),
            routing_id=uuid4(),
            endpoint_url="https://api.backend.ai/models/dep-001/routing/03",
            session_id=uuid4(),
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
mock_model_deployment_id_1 = "8c3105c3-3a02-42e3-aa00-6923cdcd114c"
mock_created_user_id_1 = "9a41b189-72fa-4265-afe8-04172ec5d26b"
mock_model_deployment_1 = ModelDeployment(
    id=UUID(mock_model_deployment_id_1),
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
        access_tokens=AccessTokenConnection(
            edges=[
                AccessTokenEdge(node=mock_access_token_1, cursor="token-cursor-1"),
                AccessTokenEdge(node=mock_access_token_2, cursor="token-cursor-2"),
                AccessTokenEdge(node=mock_access_token_3, cursor="token-cursor-3"),
                AccessTokenEdge(node=mock_access_token_4, cursor="token-cursor-4"),
                AccessTokenEdge(node=mock_access_token_5, cursor="token-cursor-5"),
            ],
            page_info=PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor="token-cursor-1",
                end_cursor="token-cursor-5",
            ),
        ),
    ),
    revision=mock_model_revision_1,
    revision_history=ModelRevisionConnection(
        count=2,
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
    scaling_rule=ScalingRule(auto_scaling_rules=[mock_scaling_rule_1, mock_scaling_rule_2]),
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
    default_deployment_strategy=DeploymentStrategy(type=DeploymentStrategyType.ROLLING),
    created_user=User(
        id=UUID(mock_created_user_id_1),
        username="admin",
        email="admin@backend.ai",
        need_password_change=False,
        full_name="System Administrator",
        description="Primary deployment administrator",
        status="active",
        status_info="Normal operation",
        created_at=datetime.now() - timedelta(days=365),
        modified_at=datetime.now() - timedelta(days=7),
        domain_name="default",
        role="superadmin",
        resource_policy="default",
        allowed_client_ip=[],
        totp_activated=False,
        totp_activated_at=datetime.now() - timedelta(days=365),
        sudo_session_enabled=True,
        container_uid=1000,
        container_main_gid=1000,
        container_gids=[1000],
    ),
)

mock_model_deployment_id_2 = "5f839a95-17bd-43b0-a029-a132aa60ae71"
mock_created_user_id_2 = "75994553-fa63-4464-9398-67b6b96c8d11"
mock_model_deployment_2 = ModelDeployment(
    id=UUID(mock_model_deployment_id_2),
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
        access_tokens=AccessTokenConnection(
            edges=[
                AccessTokenEdge(node=mock_access_token_1, cursor="token-cursor-1"),
                AccessTokenEdge(node=mock_access_token_2, cursor="token-cursor-2"),
            ],
            page_info=PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor="token-cursor-1",
                end_cursor="token-cursor-5",
            ),
        ),
    ),
    revision=mock_model_revision_3,
    revision_history=ModelRevisionConnection(
        count=1,
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
    default_deployment_strategy=DeploymentStrategy(type=DeploymentStrategyType.BLUE_GREEN),
    created_user=User(
        id=UUID(mock_created_user_id_2),
        username="mlops_user",
        email="mlops@backend.ai",
        need_password_change=False,
        full_name="MLOps Team",
        description="MLOps team deployment account",
        status="active",
        status_info="Normal operation",
        created_at=datetime.now() - timedelta(days=180),
        modified_at=datetime.now() - timedelta(days=2),
        domain_name="default",
        role="admin",
        resource_policy="default",
        allowed_client_ip=[],
        totp_activated=False,
        totp_activated_at=datetime.now() - timedelta(days=180),
        sudo_session_enabled=False,
        container_uid=1001,
        container_main_gid=1001,
        container_gids=[1001],
    ),
)

mock_model_deployment_id_3 = "d040c413-a5df-4292-a5f4-0e0d85f7a1d4"
mock_created_user_id_3 = "640b0af8-8140-4e58-8ca4-96daba325be8"
mock_model_deployment_3 = ModelDeployment(
    id=UUID(mock_model_deployment_id_3),
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
        access_tokens=AccessTokenConnection(
            edges=[
                AccessTokenEdge(node=mock_access_token_1, cursor="token-cursor-1"),
                AccessTokenEdge(node=mock_access_token_2, cursor="token-cursor-2"),
                AccessTokenEdge(node=mock_access_token_3, cursor="token-cursor-3"),
                AccessTokenEdge(node=mock_access_token_4, cursor="token-cursor-4"),
            ],
            page_info=PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor="token-cursor-1",
                end_cursor="token-cursor-5",
            ),
        ),
    ),
    revision=None,
    revision_history=ModelRevisionConnection(
        count=0,
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
    default_deployment_strategy=DeploymentStrategy(type=DeploymentStrategyType.CANARY),
    created_user=User(
        id=UUID(mock_created_user_id_3),
        username="dev_user",
        email="developer@backend.ai",
        need_password_change=False,
        full_name="Development Team",
        description="Development team deployment account",
        status="active",
        status_info="Normal operation",
        created_at=datetime.now() - timedelta(days=90),
        modified_at=datetime.now() - timedelta(days=14),
        domain_name="default",
        role="user",
        resource_policy="default",
        allowed_client_ip=[],
        totp_activated=False,
        totp_activated_at=datetime.now() - timedelta(days=90),
        sudo_session_enabled=False,
        container_uid=1002,
        container_main_gid=1002,
        container_gids=[1002],
    ),
)


ModelDeploymentEdge = Edge[ModelDeployment]


# Connection types for Relay support
@strawberry.type(description="Added in 25.13.0")
class ModelDeploymentConnection(Connection[ModelDeployment]):
    count: int

    def __init__(self, *args, count: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.count = count


async def resolve_deployments(
    info: Info[StrawberryGQLContext],
    filter: Optional[DeploymentFilter] = None,
    order_by: Optional[list[DeploymentOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> ModelDeploymentConnection:
    return ModelDeploymentConnection(
        count=3,
        edges=[
            ModelDeploymentEdge(node=mock_model_deployment_1, cursor="deployment-cursor-1"),
            ModelDeploymentEdge(node=mock_model_deployment_2, cursor="deployment-cursor-2"),
            ModelDeploymentEdge(node=mock_model_deployment_3, cursor="deployment-cursor-3"),
        ],
        page_info=PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor="deployment-cursor-1",
            end_cursor="deployment-cursor-3",
        ),
    )


# Resolvers
@strawberry.field(description="Added in 25.13.0")
async def deployments(
    info: Info[StrawberryGQLContext],
    filter: Optional[DeploymentFilter] = None,
    order_by: Optional[list[DeploymentOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> ModelDeploymentConnection:
    """List deployments with optional filtering and pagination."""

    return await resolve_deployments(
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


@strawberry.field(description="Added in 25.13.0")
async def deployment(id: ID) -> Optional[ModelDeployment]:
    """Get a specific deployment by ID."""
    return mock_model_deployment_1


@strawberry.field(description="Added in 25.13.0")
async def replica(id: ID) -> Optional[ModelReplica]:
    """Get a specific replica by ID."""

    return ModelReplica(
        id=id,
        name="llama-3-8b-instruct-replica-01",
        status=ReplicaStatus.HEALTHY,
        revision=mock_model_revision_1,
        routings=[],
    )


@strawberry.mutation(description="Added in 25.13.0")
async def create_model_deployment(
    input: CreateModelDeploymentInput,
) -> CreateModelDeploymentPayload:
    """Create a new model deployment."""
    # Create a dummy deployment for placeholder
    return CreateModelDeploymentPayload(deployment=mock_model_deployment_1)


@strawberry.mutation(description="Added in 25.13.0")
async def update_model_deployment(
    input: UpdateModelDeploymentInput,
) -> UpdateModelDeploymentPayload:
    """Update an existing model deployment."""
    # Create a dummy deployment for placeholder
    return UpdateModelDeploymentPayload(deployment=mock_model_deployment_1)


@strawberry.mutation(description="Added in 25.13.0")
async def delete_model_deployment(
    input: DeleteModelDeploymentInput,
) -> DeleteModelDeploymentPayload:
    """Delete a model deployment."""
    return DeleteModelDeploymentPayload(deployment=None)


@strawberry.subscription(description="Added in 25.13.0")
async def deployment_status_changed(
    deployment_id: ID,
) -> AsyncGenerator[DeploymentStatusChangedPayload, None]:
    """Subscribe to deployment status changes."""
    deployment = [mock_model_deployment_1, mock_model_deployment_2, mock_model_deployment_3]

    for dep in deployment:
        yield DeploymentStatusChangedPayload(deployment=dep)


@strawberry.subscription(description="Added in 25.13.0")
async def replica_status_changed(
    revision_id: ID,
) -> AsyncGenerator[ReplicaStatusChangedPayload, None]:
    """Subscribe to replica status changes."""
    replicas = [mock_model_replica_1, mock_model_replica_2, mock_model_replica_3]

    for replica in replicas:
        yield ReplicaStatusChangedPayload(replica=replica)
