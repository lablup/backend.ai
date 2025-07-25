from datetime import datetime
from enum import StrEnum
from typing import Annotated, AsyncGenerator, Optional, cast

import strawberry
from strawberry import ID, Info, relay
from strawberry.relay import Connection, Node, NodeID
from strawberry.relay.types import NodeIterableType

from ai.backend.manager.api.gql.federated_types import (
    AccessToken,
    AutoScalingRule,
    Domain,
    Image,
    Project,
    ResourceGroup,
    User,
    VFolder,
)
from ai.backend.manager.api.gql.model_deployment.routing import RoutingNode
from ai.backend.manager.api.gql.types import JSONString, OrderDirection, StringFilter

from .model_revision import (
    ClusterConfig,
    ClusterConfigInput,
    ClusterMode,
    CreateModelRevisionInput,
    ModelRevision,
    ModelRuntimeConfig,
    ModelVFolderConfig,
    ResourceConfig,
)


@strawberry.enum
class DeploymentStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


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


# Strategy Config Types
@strawberry.type
class RollingConfig:
    max_surge: int
    max_unavailable: int


@strawberry.type
class BlueGreenConfig:
    auto_promotion_enabled: bool
    termination_wait_time: int


@strawberry.type
class CanaryConfig:
    canary_percentage: int
    canary_duration: str
    success_threshold: float


DeploymentStrategyConfig = Annotated[
    RollingConfig | BlueGreenConfig | CanaryConfig,
    strawberry.union(
        "DeploymentStrategyConfig", description="Different deployment strategy configurations"
    ),
]


@strawberry.type
class DeploymentStrategy:
    type: DeploymentStrategyType
    config: DeploymentStrategyConfig


@strawberry.type
class ModelReplica(Node):
    id: NodeID
    name: str
    revision: ModelRevision
    routings: list[RoutingNode]


@strawberry.type
class ReplicaManagement:
    desired_replica_count: int
    replicas: list[ModelReplica]
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
    revision_history: list[ModelRevision]

    replica_management: ReplicaManagement

    deployment_strategy: DeploymentStrategy

    # Federated types from existing schema
    domain: Domain
    project: Project
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
    domain: Optional[StringFilter] = None
    project: Optional[StringFilter] = None

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
    deployment: ModelDeployment


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


@strawberry.input(one_of=True)
class DeploymentStrategyConfigInput:
    rolling: strawberry.Maybe[RollingConfigInput]
    blue_green: strawberry.Maybe[BlueGreenConfigInput]
    canary: strawberry.Maybe[CanaryConfigInput]


@strawberry.input
class DeploymentStrategyInput:
    type: DeploymentStrategyType
    config: DeploymentStrategyConfigInput


@strawberry.input
class CreateModelDeploymentInput:
    name: str
    preferred_domain_name: Optional[str] = None
    domain: str
    project: str
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


# Connection types for Relay support
@strawberry.type
class ModelDeploymentConnection(Connection[ModelDeployment]):
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


@strawberry.type
class ModelReplicaConnection(Connection[ModelReplica]):
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
class ModelRevisionConnection(Connection[ModelRevision]):
    @classmethod
    def resolve_connection(
        cls,
        nodes: NodeIterableType[ModelRevision],
        *,
        info: Info,
        before: Optional[str] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        last: Optional[int] = None,
        max_results: Optional[int] = None,
        **kwargs,
    ) -> "ModelRevisionConnection":
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
    return []


@strawberry.field
async def deployment(id: ID) -> Optional[ModelDeployment]:
    """Get a specific deployment by ID."""
    return ModelDeployment(
        id=ID("placeholder-id"),
        name="placeholder",
        status=DeploymentStatus.ACTIVE,
        open_to_public=False,
        tags=[],
        revision_history=[],
        replica_management=ReplicaManagement(
            desired_replica_count=1, replicas=[], auto_scaling_rules=[]
        ),
        deployment_strategy=DeploymentStrategy(
            type=DeploymentStrategyType.ROLLING,
            config=RollingConfig(max_surge=1, max_unavailable=0),
        ),
        domain=Domain(id=ID("domain-id")),
        project=Project(id=ID("project-id")),
        created_user=User(id=ID("user-id")),
        resource_group=ResourceGroup(id=ID("rg-id")),
        access_tokens=[],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@strawberry.field
async def deployment_metrics(
    id: ID,
    filter: Optional[DeploymentMetricsFilter] = None,
) -> list[DeploymentMetrics]:
    """Get metrics for a deployment."""
    return []


@strawberry.field
async def replica(id: ID) -> Optional[ModelReplica]:
    """Get a specific replica by ID."""
    return None


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
        revision_history=[],
        replica_management=ReplicaManagement(
            desired_replica_count=1, replicas=[], auto_scaling_rules=[]
        ),
        deployment_strategy=DeploymentStrategy(
            type=DeploymentStrategyType.ROLLING,
            config=RollingConfig(max_surge=1, max_unavailable=0),
        ),
        domain=Domain(id=ID("domain-id")),
        project=Project(id=ID("project-id")),
        created_user=User(id=ID("user-id")),
        resource_group=ResourceGroup(id=ID("rg-id")),
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
        revision_history=[],
        replica_management=ReplicaManagement(
            desired_replica_count=1, replicas=[], auto_scaling_rules=[]
        ),
        deployment_strategy=DeploymentStrategy(
            type=DeploymentStrategyType.ROLLING,
            config=RollingConfig(max_surge=1, max_unavailable=0),
        ),
        domain=Domain(id=ID("domain-id")),
        project=Project(id=ID("project-id")),
        created_user=User(id=ID("user-id")),
        resource_group=ResourceGroup(id=ID("rg-id")),
        access_tokens=[],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    return UpdateModelDeploymentPayload(deployment=deployment)


@strawberry.mutation
async def delete_model_deployment(id: ID) -> ID:
    """Delete a model deployment."""
    return id


@strawberry.subscription
async def deployment_status_changed(deployment_id: ID) -> AsyncGenerator[ModelDeployment, None]:
    """Subscribe to deployment status changes."""

    async def deployment_generator():
        # This would yield deployment updates in a real implementation
        yield ModelDeployment(
            id=ID("placeholder-id"),
            name="placeholder",
            status=DeploymentStatus.ACTIVE,
            open_to_public=False,
            tags=[],
            revision_history=[],
            replica_management=ReplicaManagement(
                desired_replica_count=1, replicas=[], auto_scaling_rules=[]
            ),
            deployment_strategy=DeploymentStrategy(
                type=DeploymentStrategyType.ROLLING,
                config=RollingConfig(max_surge=1, max_unavailable=0),
            ),
            domain=Domain(id=ID("domain-id")),
            project=Project(id=ID("project-id")),
            created_user=User(id=ID("user-id")),
            resource_group=ResourceGroup(id=ID("rg-id")),
            access_tokens=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    # Return async generator
    return deployment_generator()


@strawberry.subscription
async def replica_status_changed(revision_id: ID) -> AsyncGenerator[ModelReplica, None]:
    """Subscribe to replica status changes."""

    async def replica_generator():
        # This would yield replica updates in a real implementation
        yield ModelReplica(
            id=revision_id,
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

    # Return async generator
    return replica_generator()


@strawberry.subscription
async def metrics_updated(deployment_id: ID) -> AsyncGenerator[DeploymentMetrics, None]:
    """Subscribe to metrics updates."""

    async def metrics_generator():
        # This would yield metrics updates in a real implementation
        yield DeploymentMetrics(replica_metrics=[])

    # Return async generator
    return metrics_generator()
