from datetime import datetime, timedelta
from enum import StrEnum
from typing import AsyncGenerator, Optional
from uuid import UUID, uuid4

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID, PageInfo

from ai.backend.common.data.model_deployment.types import (
    DeploymentStrategy as CommonDeploymentStrategy,
)
from ai.backend.common.data.model_deployment.types import (
    ModelDeploymentStatus as CommonDeploymentStatus,
)
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.domain import Domain, mock_domain
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
from ai.backend.manager.api.gql.model_deployment.model_replica import (
    ModelReplicaConnection,
    ModelReplicaEdge,
    ReplicaFilter,
    ReplicaOrderBy,
    mock_model_replica_1,
    mock_model_replica_2,
    mock_model_replica_3,
)
from ai.backend.manager.api.gql.project import Project, mock_project
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.user import User, mock_user_id

from .model_revision import (
    CreateModelRevisionInput,
    ModelRevision,
    ModelRevisionConnection,
    ModelRevisionEdge,
    ModelRevisionFilter,
    ModelRevisionOrderBy,
    mock_model_revision_1,
    mock_model_revision_2,
    mock_model_revision_3,
)

DeploymentStatus = strawberry.enum(
    CommonDeploymentStatus,
    name="DeploymentStatus",
    description="Added in 25.13.0. This enum represents the deployment status of a model deployment, indicating its current state.",
)

DeploymentStrategyType = strawberry.enum(
    CommonDeploymentStrategy,
    name="DeploymentStrategyType",
    description="Added in 25.13.0. This enum represents the deployment strategy type of a model deployment, indicating the strategy used for deployment.",
)


@strawberry.enum(description="Added in 25.13.0")
class DeploymentOrderField(StrEnum):
    CREATED_AT = "CREATED_AT"
    UPDATED_AT = "UPDATED_AT"
    NAME = "NAME"


@strawberry.type(description="Added in 25.13.0")
class DeploymentStrategy:
    type: DeploymentStrategyType


@strawberry.type(description="Added in 25.13.0")
class ReplicaState:
    desired_replica_count: int
    _replica_ids: strawberry.Private[list[UUID]]

    @strawberry.field
    async def replicas(
        self,
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
            count=2,
            edges=[
                ModelReplicaEdge(node=mock_model_replica_1, cursor="replica-cursor-1"),
                ModelReplicaEdge(node=mock_model_replica_2, cursor="replica-cursor-2"),
            ],
        )


@strawberry.type(description="Added in 25.13.0")
class ScalingRule:
    auto_scaling_rules: list[AutoScalingRule]


@strawberry.type(description="Added in 25.13.0")
class ModelDeploymentMetadata:
    name: str
    status: DeploymentStatus
    tags: list[str]
    project: Project
    domain: Domain
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
    scaling_rule: ScalingRule
    replica_state: ReplicaState
    default_deployment_strategy: DeploymentStrategy
    created_user: User

    @strawberry.field
    async def revision_history(
        self,
        info: Info[StrawberryGQLContext],
        filter: Optional[ModelRevisionFilter] = None,
        order_by: Optional[list[ModelRevisionOrderBy]] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        last: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> ModelRevisionConnection:
        return ModelRevisionConnection(
            count=2,
            edges=[
                ModelRevisionEdge(node=mock_model_revision_1, cursor="rev-cursor-1"),
                ModelRevisionEdge(node=mock_model_revision_2, cursor="rev-cursor-2"),
            ],
        )


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
    endpoint_url: Optional[StringFilter] = None
    id: Optional[ID] = None

    AND: Optional[list["DeploymentFilter"]] = None
    OR: Optional[list["DeploymentFilter"]] = None
    NOT: Optional[list["DeploymentFilter"]] = None


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
    deployment: ModelDeployment


@strawberry.type(description="Added in 25.13.0")
class DeleteModelDeploymentPayload:
    id: ID


@strawberry.type(description="Added in 25.13.0")
class DeploymentStatusChangedPayload:
    deployment: ModelDeployment


# Input Types
@strawberry.input(description="Added in 25.13.0")
class ModelDeploymentMetadataInput:
    project_id: ID
    domain_name: str
    name: Optional[str] = None
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
    desired_replica_count: Optional[int] = None
    name: Optional[str] = None
    preferred_domain_name: Optional[str] = None


@strawberry.input(description="Added in 25.13.0")
class DeleteModelDeploymentInput:
    id: ID


# TODO: After implementing the actual logic, remove these mock objects
# Mock Model Deployments
mock_model_deployment_id_1 = "8c3105c3-3a02-42e3-aa00-6923cdcd114c"
mock_created_user_id_1 = "9a41b189-72fa-4265-afe8-04172ec5d26b"
mock_model_deployment_1 = ModelDeployment(
    id=UUID(mock_model_deployment_id_1),
    metadata=ModelDeploymentMetadata(
        name="Llama 3.8B Instruct",
        status=DeploymentStatus.READY,
        tags=["production", "llm", "chat", "instruct"],
        created_at=datetime.now() - timedelta(days=30),
        updated_at=datetime.now() - timedelta(hours=2),
        project=mock_project,
        domain=mock_domain,
    ),
    network_access=ModelDeploymentNetworkAccess(
        endpoint_url="https://api.backend.ai/models/dep-001",
        preferred_domain_name="llama-3-8b.models.backend.ai",
        open_to_public=True,
        access_tokens=AccessTokenConnection(
            count=5,
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
    scaling_rule=ScalingRule(auto_scaling_rules=[mock_scaling_rule_1, mock_scaling_rule_2]),
    replica_state=ReplicaState(
        desired_replica_count=3,
        _replica_ids=[mock_model_replica_1.id, mock_model_replica_2.id, mock_model_replica_3.id],
    ),
    default_deployment_strategy=DeploymentStrategy(type=DeploymentStrategyType.ROLLING),
    created_user=User(id=mock_user_id),
)

mock_model_deployment_id_2 = "5f839a95-17bd-43b0-a029-a132aa60ae71"
mock_created_user_id_2 = "75994553-fa63-4464-9398-67b6b96c8d11"
mock_model_deployment_2 = ModelDeployment(
    id=UUID(mock_model_deployment_id_2),
    metadata=ModelDeploymentMetadata(
        name="Mistral 7B v0.3",
        status=DeploymentStatus.READY,
        tags=["staging", "llm", "experimental"],
        created_at=datetime.now() - timedelta(days=20),
        updated_at=datetime.now() - timedelta(days=1),
        project=mock_project,
        domain=mock_domain,
    ),
    network_access=ModelDeploymentNetworkAccess(
        endpoint_url="https://api.backend.ai/models/dep-002",
        preferred_domain_name="mistral-7b.models.backend.ai",
        open_to_public=False,
        access_tokens=AccessTokenConnection(
            count=2,
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
    scaling_rule=ScalingRule(auto_scaling_rules=[]),
    replica_state=ReplicaState(
        desired_replica_count=1,
        _replica_ids=[mock_model_replica_3.id],
    ),
    default_deployment_strategy=DeploymentStrategy(type=DeploymentStrategyType.BLUE_GREEN),
    created_user=User(id=mock_user_id),
)

mock_model_deployment_id_3 = "d040c413-a5df-4292-a5f4-0e0d85f7a1d4"
mock_created_user_id_3 = "640b0af8-8140-4e58-8ca4-96daba325be8"
mock_model_deployment_3 = ModelDeployment(
    id=UUID(mock_model_deployment_id_3),
    metadata=ModelDeploymentMetadata(
        name="Gemma 2.9B",
        status=DeploymentStatus.STOPPED,
        project=mock_project,
        domain=mock_domain,
        tags=["development", "llm", "testing"],
        created_at=datetime.now() - timedelta(days=15),
        updated_at=datetime.now() - timedelta(days=7),
    ),
    network_access=ModelDeploymentNetworkAccess(
        endpoint_url=None,
        preferred_domain_name=None,
        open_to_public=False,
        access_tokens=AccessTokenConnection(
            count=4,
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
                end_cursor="token-cursor-4",
            ),
        ),
    ),
    revision=None,
    scaling_rule=ScalingRule(auto_scaling_rules=[]),
    replica_state=ReplicaState(
        desired_replica_count=0,
        _replica_ids=[],
    ),
    default_deployment_strategy=DeploymentStrategy(type=DeploymentStrategyType.BLUE_GREEN),
    created_user=User(id=mock_user_id),
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


@strawberry.mutation(description="Added in 25.13.0")
async def create_model_deployment(
    input: CreateModelDeploymentInput, info: Info[StrawberryGQLContext]
) -> CreateModelDeploymentPayload:
    """Create a new model deployment."""
    # Create a dummy deployment for placeholder
    return CreateModelDeploymentPayload(deployment=mock_model_deployment_1)


@strawberry.mutation(description="Added in 25.13.0")
async def update_model_deployment(
    input: UpdateModelDeploymentInput, info: Info[StrawberryGQLContext]
) -> UpdateModelDeploymentPayload:
    """Update an existing model deployment."""
    # Create a dummy deployment for placeholder
    return UpdateModelDeploymentPayload(deployment=mock_model_deployment_1)


@strawberry.mutation(description="Added in 25.13.0")
async def delete_model_deployment(
    input: DeleteModelDeploymentInput, info: Info[StrawberryGQLContext]
) -> DeleteModelDeploymentPayload:
    """Delete a model deployment."""
    return DeleteModelDeploymentPayload(id=ID(str(uuid4())))


@strawberry.subscription(description="Added in 25.13.0")
async def deployment_status_changed(
    deployment_id: ID, info: Info[StrawberryGQLContext]
) -> AsyncGenerator[DeploymentStatusChangedPayload, None]:
    """Subscribe to deployment status changes."""
    deployment = [mock_model_deployment_1, mock_model_deployment_2, mock_model_deployment_3]

    for dep in deployment:
        yield DeploymentStatusChangedPayload(deployment=dep)


@strawberry.input(description="Added in 25.13.0")
class SyncReplicaInput:
    model_deployment_id: ID


@strawberry.type(description="Added in 25.13.0")
class SyncReplicaPayload:
    success: bool


@strawberry.mutation(
    description="Added in 25.13.0. Force syncs up-to-date replica information. In normal situations this will be automatically handled by Backend.AI schedulers"
)
async def sync_replicas(
    input: SyncReplicaInput, info: Info[StrawberryGQLContext]
) -> SyncReplicaPayload:
    return SyncReplicaPayload(success=True)
