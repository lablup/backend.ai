"""Deployment GraphQL types."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any, Self, cast
from uuid import UUID

import strawberry
from strawberry import ID, UNSET, Info
from strawberry.relay import Connection, Edge, NodeID, PageInfo

from ai.backend.common.data.model_deployment.types import (
    ModelDeploymentStatus,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    AdminSearchRevisionsInput,
    SearchAccessTokensInput,
    SearchAutoScalingRulesInput,
    SearchReplicasInput,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    CreateDeploymentInput as CreateDeploymentInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    DeleteDeploymentInput as DeleteDeploymentInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    DeploymentFilter as DeploymentFilterDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    DeploymentOrder as DeploymentOrderDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    DeploymentStatusFilter as DeploymentStatusFilterDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    DeploymentStrategyInput as DeploymentStrategyInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    ModelDeploymentMetadataInput as ModelDeploymentMetadataInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    ModelDeploymentNetworkAccessInput as ModelDeploymentNetworkAccessInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    SyncReplicaInput as SyncReplicaInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    UpdateDeploymentInput as UpdateDeploymentInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    CreateDeploymentPayload as CreateDeploymentPayloadDTO,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    DeleteDeploymentPayload as DeleteDeploymentPayloadDTO,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    DeploymentNode as DeploymentNodeDTO,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    DeploymentStatusChangedPayload as DeploymentStatusChangedPayloadDTO,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    SyncReplicaPayload as SyncReplicaPayloadDTO,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    UpdateDeploymentPayload as UpdateDeploymentPayloadDTO,
)
from ai.backend.common.dto.manager.v2.deployment.types import (
    DeploymentMetadataInfoDTO,
    DeploymentNetworkAccessInfoDTO,
    DeploymentStrategyInfoDTO,
    ReplicaStateInfo,
)
from ai.backend.common.dto.manager.v2.deployment.types import (
    ProjectDeploymentScope as ProjectDeploymentScopeDTO,
)
from ai.backend.manager.api.gql.base import (
    OrderDirection,
    StringFilter,
    encode_cursor,
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
from ai.backend.manager.api.gql.deployment.types.access_token import (
    AccessToken,
    AccessTokenConnection,
    AccessTokenEdge,
    AccessTokenFilter,
    AccessTokenOrderBy,
)
from ai.backend.manager.api.gql.deployment.types.auto_scaling import (
    AutoScalingRule,
    AutoScalingRuleConnection,
    AutoScalingRuleEdge,
    AutoScalingRuleFilter,
    AutoScalingRuleOrderBy,
)
from ai.backend.manager.api.gql.deployment.types.policy import (
    BlueGreenConfigInputGQL,
    DeploymentPolicyGQL,
    DeploymentStrategyTypeGQL,
    RollingUpdateConfigInputGQL,
)
from ai.backend.manager.api.gql.deployment.types.replica import (
    ModelReplica,
    ModelReplicaConnection,
    ModelReplicaEdge,
    ReplicaFilter,
    ReplicaOrderBy,
)
from ai.backend.manager.api.gql.deployment.types.revision import (
    CreateRevisionInput,
    ModelRevision,
    ModelRevisionConnection,
    ModelRevisionEdge,
    ModelRevisionFilter,
    ModelRevisionOrderBy,
)
from ai.backend.manager.api.gql.domain import Domain
from ai.backend.manager.api.gql.project import Project
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.user_federation import User
from ai.backend.manager.api.gql_legacy.domain import DomainNode
from ai.backend.manager.api.gql_legacy.group import GroupNode
from ai.backend.manager.api.gql_legacy.user import UserNode
from ai.backend.manager.data.deployment.types import (
    AccessTokenSearchScope,
    AutoScalingRuleSearchScope,
    DeploymentOrderField,
    ReplicaSearchScope,
    RevisionSearchScope,
)

DeploymentStatusGQL: type[ModelDeploymentStatus] = gql_enum(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="This enum represents the deployment status of a model deployment, indicating its current state.",
    ),
    ModelDeploymentStatus,
    name="DeploymentStatus",
)


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="Represents the deployment strategy configuration that determines how updates are rolled out to replicas (e.g., rolling update, blue-green).",
    ),
    model=DeploymentStrategyInfoDTO,
)
class DeploymentStrategyGQL:
    type: DeploymentStrategyTypeGQL


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="Represents the current replica state of a deployment, including the desired replica count and access to the list of active replicas.",
    ),
    model=ReplicaStateInfo,
)
class ReplicaState:
    desired_replica_count: int


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="Contains metadata information for a model deployment including its name, status, tags, and timestamps. Also provides access to the associated project and domain.",
    ),
    model=DeploymentMetadataInfoDTO,
)
class ModelDeploymentMetadata:
    project_id: ID
    domain_name: str
    name: str
    status: DeploymentStatusGQL
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    @gql_field(description="The project of this entity.")  # type: ignore[misc]
    async def project(self, info: Info[StrawberryGQLContext]) -> Project:
        project_global_id = to_global_id(
            GroupNode, UUID(str(self.project_id)), is_target_graphene_object=True
        )
        return Project(id=ID(project_global_id))

    @gql_field(description="The domain of this entity.")  # type: ignore[misc]
    async def domain(self, info: Info[StrawberryGQLContext]) -> Domain:
        domain_global_id = to_global_id(
            DomainNode, self.domain_name, is_target_graphene_object=True
        )
        return Domain(id=ID(domain_global_id))


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="Provides network access configuration for a model deployment, including the endpoint URL, preferred domain name, and public access settings. Also manages access tokens for authentication.",
    ),
    model=DeploymentNetworkAccessInfoDTO,
)
class ModelDeploymentNetworkAccess:
    endpoint_url: str | None = None
    preferred_domain_name: str | None = None
    open_to_public: bool = False


# Main ModelDeployment Type
@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="Represents a model deployment in Backend.AI. A deployment is a long-running inference service that exposes a trained model via HTTP endpoints. Deployments manage the lifecycle of model replicas, handle traffic routing, and provide auto-scaling capabilities based on configured rules.",
    )
)
class ModelDeployment(PydanticNodeMixin[DeploymentNodeDTO]):
    id: NodeID[str]
    metadata: ModelDeploymentMetadata
    network_access: ModelDeploymentNetworkAccess
    current_revision_id: ID | None = None
    default_deployment_strategy: DeploymentStrategyGQL
    replica_state: ReplicaState
    created_user_id: ID

    @gql_field(description="The created user of this entity.")  # type: ignore[misc]
    async def created_user(self, info: Info[StrawberryGQLContext]) -> User:
        user_global_id = to_global_id(
            UserNode, UUID(str(self.created_user_id)), is_target_graphene_object=True
        )
        return User(id=strawberry.ID(user_global_id))

    @gql_added_field(
        BackendAIGQLMeta(added_version="25.19.0", description="Deployment policy configuration.")
    )  # type: ignore[misc]
    async def deployment_policy(
        self, info: Info[StrawberryGQLContext]
    ) -> DeploymentPolicyGQL | None:
        """Get the deployment policy for this deployment."""
        policy_data = await info.context.data_loaders.deployment_policy_by_endpoint_loader.load(
            UUID(str(self.id))
        )
        if policy_data is None:
            return None
        return policy_data

    @gql_field(description="The revision history of this entity.")  # type: ignore[misc]
    async def revision_history(
        self,
        info: Info[StrawberryGQLContext],
        filter: ModelRevisionFilter | None = None,
        order_by: list[ModelRevisionOrderBy] | None = None,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> ModelRevisionConnection:
        pydantic_filter = filter.to_pydantic() if filter else None
        pydantic_order = [o.to_pydantic() for o in order_by] if order_by else None
        payload = await info.context.adapters.deployment.search_revisions(
            scope=RevisionSearchScope(deployment_id=UUID(str(self.id))),
            input=AdminSearchRevisionsInput(
                filter=pydantic_filter,
                order=pydantic_order,
                first=first,
                after=after,
                last=last,
                before=before,
                limit=limit,
                offset=offset,
            ),
        )
        nodes = [ModelRevision.from_pydantic(item) for item in payload.items]
        edges = [ModelRevisionEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
        return ModelRevisionConnection(
            count=payload.total_count,
            edges=edges,
            page_info=PageInfo(
                has_next_page=payload.has_next_page,
                has_previous_page=payload.has_previous_page,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
        )

    @gql_field(description="The replicas of this entity.")  # type: ignore[misc]
    async def replicas(
        self,
        info: Info[StrawberryGQLContext],
        filter: ReplicaFilter | None = None,
        order_by: list[ReplicaOrderBy] | None = None,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> ModelReplicaConnection:
        pydantic_filter = filter.to_pydantic() if filter else None
        pydantic_order = [o.to_pydantic() for o in order_by] if order_by else None
        payload = await info.context.adapters.deployment.search_replicas(
            scope=ReplicaSearchScope(deployment_id=UUID(str(self.id))),
            input=SearchReplicasInput(
                filter=pydantic_filter,
                order=pydantic_order,
                first=first,
                after=after,
                last=last,
                before=before,
                limit=limit,
                offset=offset,
            ),
        )
        nodes = [ModelReplica.from_pydantic(item) for item in payload.items]
        edges = [ModelReplicaEdge(node=node, cursor=str(node.id)) for node in nodes]
        return ModelReplicaConnection(
            count=payload.total_count,
            edges=edges,
            page_info=PageInfo(
                has_next_page=payload.has_next_page,
                has_previous_page=payload.has_previous_page,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
        )

    @gql_field(description="The auto scaling rules of this entity.")  # type: ignore[misc]
    async def auto_scaling_rules(
        self,
        info: Info[StrawberryGQLContext],
        filter: AutoScalingRuleFilter | None = None,
        order_by: list[AutoScalingRuleOrderBy] | None = None,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> AutoScalingRuleConnection:
        pydantic_filter = filter.to_pydantic() if filter else None
        pydantic_order = [o.to_pydantic() for o in order_by] if order_by else None
        payload = await info.context.adapters.deployment.search_rules(
            scope=AutoScalingRuleSearchScope(deployment_id=UUID(str(self.id))),
            input=SearchAutoScalingRulesInput(
                filter=pydantic_filter,
                order=pydantic_order,
                first=first,
                after=after,
                last=last,
                before=before,
                limit=limit,
                offset=offset,
            ),
        )
        nodes = [AutoScalingRule.from_pydantic(item) for item in payload.items]
        edges = [
            AutoScalingRuleEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes
        ]
        return AutoScalingRuleConnection(
            count=payload.total_count,
            edges=edges,
            page_info=PageInfo(
                has_next_page=payload.has_next_page,
                has_previous_page=payload.has_previous_page,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
        )

    @gql_field(description="The access tokens of this entity.")  # type: ignore[misc]
    async def access_tokens(
        self,
        info: Info[StrawberryGQLContext],
        filter: AccessTokenFilter | None = None,
        order_by: list[AccessTokenOrderBy] | None = None,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> AccessTokenConnection:
        pydantic_filter = filter.to_pydantic() if filter else None
        pydantic_order = [o.to_pydantic() for o in order_by] if order_by else None
        payload = await info.context.adapters.deployment.search_access_tokens(
            scope=AccessTokenSearchScope(deployment_id=UUID(str(self.id))),
            input=SearchAccessTokensInput(
                filter=pydantic_filter,
                order=pydantic_order,
                first=first,
                after=after,
                last=last,
                before=before,
                limit=limit,
                offset=offset,
            ),
        )
        nodes = [AccessToken.from_pydantic(item) for item in payload.items]
        edges = [AccessTokenEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
        return AccessTokenConnection(
            count=payload.total_count,
            edges=edges,
            page_info=PageInfo(
                has_next_page=payload.has_next_page,
                has_previous_page=payload.has_previous_page,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
        )

    @classmethod
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.deployment_loader.load_many([
            UUID(nid) for nid in node_ids
        ])
        return cast(list[Self | None], results)


# Filter Types
@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
)
class DeploymentStatusFilter(PydanticInputMixin[DeploymentStatusFilterDTO]):
    in_: list[DeploymentStatusGQL] | None = gql_field(
        description="The in  field.", name="in", default=None
    )
    equals: DeploymentStatusGQL | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Scope for project-level deployment operations.",
        added_version="25.19.0",
    ),
    name="ProjectDeploymentScope",
)
class ProjectDeploymentScopeGQL(PydanticInputMixin[ProjectDeploymentScopeDTO]):
    project_id: UUID = gql_field(description="Project UUID to scope the deployment operation.")


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
    name="DeploymentFilter",
)
class DeploymentFilter(PydanticInputMixin[DeploymentFilterDTO]):
    name: StringFilter | None = None
    status: DeploymentStatusFilter | None = None
    open_to_public: bool | None = None
    tags: StringFilter | None = None
    endpoint_url: StringFilter | None = None

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
)
class DeploymentOrderBy(PydanticInputMixin[DeploymentOrderDTO]):
    field: DeploymentOrderField
    direction: OrderDirection = OrderDirection.DESC


# Payload Types
@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.19.0", description="Payload for creating a model deployment."
    ),
    model=CreateDeploymentPayloadDTO,
)
class CreateDeploymentPayload:
    deployment: ModelDeployment


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.19.0", description="Payload for updating a model deployment."
    ),
    model=UpdateDeploymentPayloadDTO,
)
class UpdateDeploymentPayload:
    deployment: ModelDeployment


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.19.0", description="Payload for deleting a model deployment."
    ),
    model=DeleteDeploymentPayloadDTO,
)
class DeleteDeploymentPayload:
    id: ID


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.19.0", description="Payload for deployment status changed event."
    ),
    model=DeploymentStatusChangedPayloadDTO,
)
class DeploymentStatusChangedPayload:
    deployment: ModelDeployment


# Input Types
@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
)
class ModelDeploymentMetadataInput(PydanticInputMixin[ModelDeploymentMetadataInputDTO]):
    project_id: ID
    domain_name: str
    name: str | None = None
    tags: list[str] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
)
class ModelDeploymentNetworkAccessInput(PydanticInputMixin[ModelDeploymentNetworkAccessInputDTO]):
    preferred_domain_name: str | None = None
    open_to_public: bool = False


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Deployment strategy configuration with discriminator pattern.",
        added_version="25.19.0",
    ),
    name="DeploymentStrategyInput",
)
class DeploymentStrategyInputGQL(PydanticInputMixin[DeploymentStrategyInputDTO]):
    """Deployment strategy input with type discriminator and optional config fields.

    The `type` field determines which config field should be provided:
    - ROLLING: requires `rolling_update` config
    - BLUE_GREEN: requires `blue_green` config
    """

    type: DeploymentStrategyTypeGQL
    rolling_update: RollingUpdateConfigInputGQL | None = None
    blue_green: BlueGreenConfigInputGQL | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
)
class CreateDeploymentInput(PydanticInputMixin[CreateDeploymentInputDTO]):
    metadata: ModelDeploymentMetadataInput
    network_access: ModelDeploymentNetworkAccessInput
    default_deployment_strategy: DeploymentStrategyInputGQL
    desired_replica_count: int
    initial_revision: CreateRevisionInput | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
)
class UpdateDeploymentInput(PydanticInputMixin[UpdateDeploymentInputDTO]):
    id: ID
    open_to_public: bool | None = UNSET
    tags: list[str] | None = UNSET
    default_deployment_strategy: DeploymentStrategyInputGQL | None = UNSET
    active_revision_id: ID | None = UNSET
    desired_replica_count: int | None = UNSET
    name: str | None = UNSET
    preferred_domain_name: str | None = UNSET


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
)
class DeleteDeploymentInput(PydanticInputMixin[DeleteDeploymentInputDTO]):
    id: ID


ModelDeploymentEdge = Edge[ModelDeployment]


# Connection types for Relay support
@gql_connection_type(
    BackendAIGQLMeta(added_version="25.19.0", description="Connection for model deployments.")
)
class ModelDeploymentConnection(Connection[ModelDeployment]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# Sync replica types
@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
)
class SyncReplicaInput(PydanticInputMixin[SyncReplicaInputDTO]):
    model_deployment_id: ID


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.19.0", description="Payload for replica sync mutation result."
    ),
    model=SyncReplicaPayloadDTO,
)
class SyncReplicaPayload:
    """Payload for replica sync mutation result."""

    success: strawberry.auto
