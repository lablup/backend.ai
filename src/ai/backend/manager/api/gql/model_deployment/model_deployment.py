from datetime import datetime, timedelta
from enum import StrEnum
from typing import AsyncGenerator, Optional, cast
from uuid import uuid4

import strawberry
from strawberry import ID, Info, relay
from strawberry.relay import Connection, Node, NodeID
from strawberry.relay.types import NodeIterableType

from ai.backend.manager.api.gql.base import JSONString, OrderDirection, StringFilter
from ai.backend.manager.api.gql.federated_types import (
    AccessToken,
    AutoScalingRule,
    Image,
    ResourceGroup,
    User,
    VFolder,
)
from ai.backend.manager.api.gql.model_deployment.routing import (
    RoutingNode,
)

from .model_revision import (
    ClusterConfig,
    ClusterConfigInput,
    ClusterMode,
    CreateModelRevisionInput,
    ModelRevision,
    ModelRevisionConnection,
    ModelRuntimeConfig,
    ModelVFolderConfig,
    Mount,
    MountPermission,
    MountType,
    ResourceConfig,
    vLLMServiceConfig,
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


@strawberry.type
class ReplicaMetric:
    replica_id: ID
    cpu_usage: float
    memory_usage: float
    request_count: int


@strawberry.type
class DeploymentMetrics:
    replica_metrics: list[ReplicaMetric]


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


@strawberry.input
class DeploymentMetricsFilter:
    replica_ids: Optional[list[ID]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    AND: Optional["DeploymentMetricsFilter"] = None
    OR: Optional["DeploymentMetricsFilter"] = None
    NOT: Optional["DeploymentMetricsFilter"] = None
    DISTINCT: Optional[bool] = None


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


@strawberry.type
class DeploymentMetricsUpdatedPayload:
    metrics: DeploymentMetrics


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
        return cls(
            edges=[],
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
    model_names = [
        "llama-3-8b-instruct",
        "mistral-7b-v0.3",
        "gemma-2-9b",
        "qwen-2.5-7b-instruct",
        "mixtral-8x7b",
    ]

    deployments = []
    for i, name in enumerate(model_names):
        deployment = ModelDeployment(
            id=ID(f"dep-{i + 1:03d}"),
            name=name,
            endpoint_url=f"https://api.backend.ai/models/dep-{i + 1:03d}" if i % 2 == 0 else None,
            preferred_domain_name=f"{name}.models.backend.ai" if i % 2 == 0 else None,
            status=DeploymentStatus.ACTIVE if i % 2 == 0 else DeploymentStatus.INACTIVE,
            open_to_public=i % 3 == 0,
            tags=["production", "llm"] if i < 2 else ["staging", "experimental"],
            revision_history=ModelRevisionConnection(
                edges=[],
                page_info=relay.PageInfo(
                    has_next_page=False,
                    has_previous_page=False,
                    start_cursor=None,
                    end_cursor=None,
                ),
            ),
            replica_management=ReplicaManagement(
                desired_replica_count=3 if i % 2 == 0 else 1,
                replicas=ModelReplicaConnection(
                    edges=[],
                    page_info=relay.PageInfo(
                        has_next_page=False,
                        has_previous_page=False,
                        start_cursor=None,
                        end_cursor=None,
                    ),
                ),
            ),
            scale=Scale(auto_scaling_rules=[]),
            deployment_strategy=DeploymentStrategy(
                type=DeploymentStrategyType.ROLLING if i < 3 else DeploymentStrategyType.BLUE_GREEN,
            ),
            created_user=User(id=ID(f"user-{i % 3 + 1}")),
            resource_group=ResourceGroup(
                id=ID(f"rg-{['us-east-1', 'us-west-2', 'eu-west-1'][i % 3]}")
            ),
            access_tokens=[],
            created_at=datetime.now() - timedelta(days=30 - i * 5),
            updated_at=datetime.now() - timedelta(days=i),
        )
        deployments.append(deployment)

    return deployments


@strawberry.field
async def deployment(id: ID) -> Optional[ModelDeployment]:
    """Get a specific deployment by ID."""
    # Return a more detailed deployment
    revision = ModelRevision(
        id=ID("rev-001"),
        name="llama-3-8b-instruct-v1",
        cluster_config=ClusterConfig(mode=ClusterMode.SINGLE_NODE, size=1),
        resource_config=ResourceConfig(
            resource_group=ResourceGroup(id=ID("rg-us-east-1")),
            resource_slots=cast(
                JSONString,
                '{"cpu": 8, "mem": "32G", "cuda.shares": 1, "cuda.device": 1}',
            ),
            resource_opts=cast(
                JSONString,
                '{"shmem": "2G", "reserved_time": "24h", "scaling_group": "us-east-1"}',
            ),
        ),
        model_runtime_config=ModelRuntimeConfig(
            runtime_variant="vllm",
            service_config=vLLMServiceConfig(
                max_model_length=4096,
                parallelism=cast(JSONString, '{"tensor_parallel_size": 1}'),
                extra_cli_parameters="--enable-prefix-caching",
            ),
            environ=cast(JSONString, '{"CUDA_VISIBLE_DEVICES": "0"}'),
        ),
        model_vfolder_config=ModelVFolderConfig(
            vfolder=VFolder(id=ID("vf-model-001")),
            mount_destination="/models",
            definition_path="models/llama-3-8b/config.yaml",
        ),
        mounts=[
            Mount(
                vfolder_id=ID("vf-cache-001"),
                destination="/cache",
                type=MountType.VOLUME,
                permission=MountPermission.READ_WRITE,
            )
        ],
        image=Image(id=ID("img-vllm-001")),
        error_data=None,
        created_at=datetime.now() - timedelta(days=10),
    )

    # Create replicas with detailed info
    replicas = []
    for i in range(3):
        replica = ModelReplica(
            id=ID(f"replica-{i + 1:02d}"),
            name=f"llama-3-8b-instruct-replica-{i + 1:02d}",
            status=ReplicaStatus.HEALTHY if i < 2 else ReplicaStatus.UNHEALTHY,
            revision=revision,
            routings=[
                RoutingNode(
                    id=ID(f"routing-{i + 1:02d}"),
                    routing_id=uuid4(),
                    endpoint=f"https://api.backend.ai/models/dep-{id}/routing/{i + 1:02d}",
                    session=uuid4(),
                    status="ACTIVE" if i < 2 else "INACTIVE",
                    traffic_ratio=0.5 if i < 2 else 0.0,
                    created_at=datetime.now() - timedelta(days=i),
                    error_data=cast(JSONString, '{"error": "No errors"}'),
                    live_stat=cast(JSONString, '{"requests": 100, "latency": 200}'),
                )
            ],
        )
        replicas.append(replica)

    replica_edges = [
        strawberry.relay.Edge(node=rep, cursor=f"cursor-{idx}") for idx, rep in enumerate(replicas)
    ]

    return ModelDeployment(
        id=id,
        name="llama-3-8b-instruct",
        endpoint_url="https://api.backend.ai/models/dep-001",
        preferred_domain_name="llama-3-8b.models.backend.ai",
        status=DeploymentStatus.ACTIVE,
        open_to_public=True,
        tags=["production", "llm", "chat"],
        revision=revision,
        revision_history=ModelRevisionConnection(
            edges=[strawberry.relay.Edge(node=revision, cursor="cursor-0")],
            page_info=relay.PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor="cursor-0",
                end_cursor="cursor-0",
            ),
        ),
        replica_management=ReplicaManagement(
            desired_replica_count=3,
            replicas=ModelReplicaConnection(
                edges=replica_edges,
                page_info=relay.PageInfo(
                    has_next_page=False,
                    has_previous_page=False,
                    start_cursor="cursor-0",
                    end_cursor="cursor-2",
                ),
            ),
        ),
        scale=Scale(
            auto_scaling_rules=[
                AutoScalingRule(id=ID("asr-cpu-001")),
                AutoScalingRule(id=ID("asr-gpu-001")),
            ]
        ),
        deployment_strategy=DeploymentStrategy(
            type=DeploymentStrategyType.ROLLING,
        ),
        created_user=User(id=ID("user-001")),
        resource_group=ResourceGroup(id=ID("rg-us-east-1")),
        access_tokens=[],
        created_at=datetime.now() - timedelta(days=30),
        updated_at=datetime.now() - timedelta(hours=2),
    )


@strawberry.field
async def deployment_metrics(
    id: ID,
    filter: Optional[DeploymentMetricsFilter] = None,
) -> list[DeploymentMetrics]:
    """Get metrics for a deployment."""
    # Return more realistic metrics
    return [
        DeploymentMetrics(
            replica_metrics=[
                ReplicaMetric(
                    replica_id=ID("replica-01"),
                    cpu_usage=65.5,
                    memory_usage=42.3,
                    request_count=1250,
                ),
                ReplicaMetric(
                    replica_id=ID("replica-02"),
                    cpu_usage=72.1,
                    memory_usage=48.7,
                    request_count=1420,
                ),
                ReplicaMetric(
                    replica_id=ID("replica-03"),
                    cpu_usage=58.9,
                    memory_usage=39.2,
                    request_count=980,
                ),
            ]
        )
    ]


@strawberry.field
async def replica(id: ID) -> Optional[ModelReplica]:
    """Get a specific replica by ID."""
    revision = ModelRevision(
        id=ID("rev-001"),
        name="llama-3-8b-instruct-v1",
        cluster_config=ClusterConfig(mode=ClusterMode.SINGLE_NODE, size=1),
        resource_config=ResourceConfig(
            resource_group=ResourceGroup(id=ID("rg-us-east-1")),
            resource_slots=cast(
                JSONString,
                '{"cpu": 8, "mem": "32G", "cuda.shares": 1}',
            ),
            resource_opts=cast(
                JSONString,
                '{"shmem": "2G"}',
            ),
        ),
        model_runtime_config=ModelRuntimeConfig(
            runtime_variant="vllm",
            service_config=None,
            environ=None,
        ),
        model_vfolder_config=ModelVFolderConfig(
            vfolder=VFolder(id=ID("vf-model-001")),
            mount_destination="/models",
            definition_path="model.yaml",
        ),
        mounts=[],
        image=Image(id=ID("img-vllm-001")),
        error_data=None,
        created_at=datetime.now() - timedelta(days=10),
    )

    return ModelReplica(
        id=id,
        name="llama-3-8b-instruct-replica-01",
        status=ReplicaStatus.HEALTHY,
        revision=revision,
        routings=[],
    )


@strawberry.mutation
async def create_model_deployment(
    input: CreateModelDeploymentInput,
) -> CreateModelDeploymentPayload:
    """Create a new model deployment."""
    # Create a dummy deployment for placeholder
    deployment = ModelDeployment(
        id=ID("placeholder-id"),
        name="placeholder",
        status=DeploymentStatus.ACTIVE,
        open_to_public=False,
        tags=[],
        revision_history=ModelRevisionConnection(
            edges=[],
            page_info=relay.PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor=None,
                end_cursor=None,
            ),
        ),
        replica_management=ReplicaManagement(
            desired_replica_count=1,
            replicas=ModelReplicaConnection(
                edges=[],
                page_info=relay.PageInfo(
                    has_next_page=False,
                    has_previous_page=False,
                    start_cursor=None,
                    end_cursor=None,
                ),
            ),
        ),
        scale=Scale(auto_scaling_rules=[]),
        deployment_strategy=DeploymentStrategy(
            type=DeploymentStrategyType.ROLLING,
        ),
        created_user=User(id=ID("user-current")),
        resource_group=ResourceGroup(id=ID("rg-us-east-1")),
        access_tokens=[],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    return CreateModelDeploymentPayload(deployment=deployment)


@strawberry.mutation
async def update_model_deployment(
    input: UpdateModelDeploymentInput,
) -> UpdateModelDeploymentPayload:
    """Update an existing model deployment."""
    # Create a dummy deployment for placeholder
    deployment = ModelDeployment(
        id=ID("placeholder-id"),
        name="placeholder",
        status=DeploymentStatus.ACTIVE,
        open_to_public=False,
        tags=[],
        revision_history=ModelRevisionConnection(
            edges=[],
            page_info=relay.PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor=None,
                end_cursor=None,
            ),
        ),
        replica_management=ReplicaManagement(
            desired_replica_count=1,
            replicas=ModelReplicaConnection(
                edges=[],
                page_info=relay.PageInfo(
                    has_next_page=False,
                    has_previous_page=False,
                    start_cursor=None,
                    end_cursor=None,
                ),
            ),
        ),
        scale=Scale(auto_scaling_rules=[]),
        deployment_strategy=DeploymentStrategy(
            type=DeploymentStrategyType.ROLLING,
        ),
        created_user=User(id=ID("user-id")),
        resource_group=ResourceGroup(id=ID("rg-id")),
        access_tokens=[],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    return UpdateModelDeploymentPayload(deployment=deployment)


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

    yield DeploymentStatusChangedPayload(
        deployment=ModelDeployment(
            id=ID("placeholder-id"),
            name="placeholder",
            status=DeploymentStatus.ACTIVE,
            open_to_public=False,
            tags=[],
            revision_history=ModelRevisionConnection(
                edges=[],
                page_info=relay.PageInfo(
                    has_next_page=False,
                    has_previous_page=False,
                    start_cursor=None,
                    end_cursor=None,
                ),
            ),
            replica_management=ReplicaManagement(
                desired_replica_count=1,
                replicas=ModelReplicaConnection(
                    edges=[],
                    page_info=relay.PageInfo(
                        has_next_page=False,
                        has_previous_page=False,
                        start_cursor=None,
                        end_cursor=None,
                    ),
                ),
            ),
            scale=Scale(auto_scaling_rules=[]),
            deployment_strategy=DeploymentStrategy(
                type=DeploymentStrategyType.ROLLING,
            ),
            created_user=User(id=ID("user-id")),
            resource_group=ResourceGroup(id=ID("rg-id")),
            access_tokens=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
    )


@strawberry.subscription
async def replica_status_changed(
    revision_id: ID,
) -> AsyncGenerator[ReplicaStatusChangedPayload, None]:
    """Subscribe to replica status changes."""

    yield ReplicaStatusChangedPayload(
        replica=ModelReplica(
            id=revision_id,
            status=ReplicaStatus.HEALTHY,
            name="placeholder",
            revision=ModelRevision(
                id=ID("revision-id"),
                name="placeholder-revision",
                cluster_config=ClusterConfig(mode=ClusterMode.SINGLE_NODE, size=1),
                resource_config=ResourceConfig(
                    resource_group=ResourceGroup(id=ID("rg-id")),
                    resource_slots=cast(
                        JSONString,
                        '{"cpu": 1, "mem": "1G", "extra": {"gpu_type": "A100", "storage": "100GB"}}',
                    ),
                    resource_opts=cast(
                        JSONString,
                        '{"shmem": null, "extra": {"network": "high_bandwidth", "priority": "high"}}',
                    ),
                ),
                model_runtime_config=ModelRuntimeConfig(
                    runtime_variant="vllm", service_config=None, environ=None
                ),
                model_vfolder_config=ModelVFolderConfig(
                    vfolder=VFolder(id=ID("vf-id")),
                    mount_destination="/models",
                    definition_path="model.yaml",
                ),
                mounts=[],
                image=Image(id=ID("image-id")),
                error_data=None,
                created_at=datetime.now(),
            ),
            routings=[],
        )
    )


@strawberry.subscription
async def deployment_metrics_updated(
    deployment_id: ID,
) -> AsyncGenerator[DeploymentMetricsUpdatedPayload, None]:
    """Subscribe to metrics updates."""
    # Generate mock metrics
    replica_metrics = [
        ReplicaMetric(
            replica_id=ID(f"replica-{i}"),
            cpu_usage=65.0 + (i * 5),
            memory_usage=45.0 + (i * 3),
            request_count=150 + (i * 25),
        )
        for i in range(3)
    ]
    yield DeploymentMetricsUpdatedPayload(
        metrics=DeploymentMetrics(replica_metrics=replica_metrics)
    )
