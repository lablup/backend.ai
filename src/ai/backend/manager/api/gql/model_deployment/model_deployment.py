from collections.abc import Sequence
from datetime import datetime
from typing import AsyncGenerator, Optional
from uuid import UUID, uuid4

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.model_deployment.types import (
    DeploymentStrategy,
    ModelDeploymentStatus,
)
from ai.backend.common.exception import (
    InvalidAPIParameters,
    ModelDeploymentNotFound,
    ModelDeploymentUnavailable,
)
from ai.backend.manager.api.gql.base import (
    OrderDirection,
    StringFilter,
    build_page_info,
    build_pagination_options,
    resolve_global_id,
    to_global_id,
)
from ai.backend.manager.api.gql.domain import Domain
from ai.backend.manager.api.gql.model_deployment.access_token import (
    AccessToken,
    AccessTokenConnection,
    AccessTokenEdge,
    AccessTokenOrderBy,
)
from ai.backend.manager.api.gql.model_deployment.auto_scaling_rule import (
    AutoScalingRule,
)
from ai.backend.manager.api.gql.model_deployment.model_replica import (
    ModelReplicaConnection,
    ReplicaFilter,
    ReplicaOrderBy,
    resolve_replicas,
)
from ai.backend.manager.api.gql.project import Project
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.user import User
from ai.backend.manager.data.deployment.creator import DeploymentPolicyConfig, NewDeploymentCreator
from ai.backend.manager.data.deployment.types import (
    DeploymentMetadata,
    DeploymentNetworkSpec,
    DeploymentOrderField,
    ModelDeploymentData,
    ModelDeploymentMetadataInfo,
    ReplicaSpec,
    ReplicaStateData,
)
from ai.backend.manager.errors.service import DeploymentPolicyNotFound
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.gql_models.domain import DomainNode
from ai.backend.manager.models.gql_models.group import GroupNode
from ai.backend.manager.models.gql_models.user import UserNode
from ai.backend.manager.repositories.deployment.types.types import (
    AccessTokenOrderingOptions,
    DeploymentFilterOptions,
    DeploymentOrderingOptions,
    DeploymentStatusFilterType,
)
from ai.backend.manager.repositories.deployment.types.types import (
    DeploymentStatusFilter as RepoDeploymentStatusFilter,
)
from ai.backend.manager.repositories.deployment.updaters import (
    DeploymentPolicyUpdaterSpec,
    NewDeploymentUpdaterSpec,
)
from ai.backend.manager.services.deployment.actions.access_token.list_access_tokens import (
    ListAccessTokensAction,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.batch_load_auto_scaling_rules import (
    BatchLoadAutoScalingRulesAction,
)
from ai.backend.manager.services.deployment.actions.batch_load_deployments import (
    BatchLoadDeploymentsAction,
)
from ai.backend.manager.services.deployment.actions.create_deployment import (
    CreateDeploymentAction,
)
from ai.backend.manager.services.deployment.actions.deployment_policy import (
    GetDeploymentPolicyAction,
)
from ai.backend.manager.services.deployment.actions.destroy_deployment import (
    DestroyDeploymentAction,
)
from ai.backend.manager.services.deployment.actions.list_deployments import ListDeploymentsAction
from ai.backend.manager.services.deployment.actions.sync_replicas import SyncReplicaAction
from ai.backend.manager.services.deployment.actions.update_deployment import UpdateDeploymentAction
from ai.backend.manager.types import OptionalState, TriState

from .deployment_policy import (
    BlueGreenConfigInputGQL,
    DeploymentPolicyGQL,
    RollingUpdateConfigInputGQL,
)
from .model_revision import (
    CreateModelRevisionInput,
    ModelRevision,
    ModelRevisionConnection,
    ModelRevisionFilter,
    ModelRevisionOrderBy,
    resolve_revisions,
)

DeploymentStatusGQL: type[ModelDeploymentStatus] = strawberry.enum(
    ModelDeploymentStatus,
    name="DeploymentStatus",
    description="Added in 25.16.0. This enum represents the deployment status of a model deployment, indicating its current state.",
)

DeploymentStrategyTypeGQL: type[DeploymentStrategy] = strawberry.enum(
    DeploymentStrategy,
    name="DeploymentStrategyType",
    description="Added in 25.16.0. This enum represents the deployment strategy type of a model deployment, indicating the strategy used for deployment.",
)


@strawberry.type(description="Added in 25.16.0")
class DeploymentStrategyGQL:
    type: DeploymentStrategyTypeGQL


@strawberry.type(description="Added in 25.16.0")
class ReplicaState:
    _replica_ids: strawberry.Private[list[UUID]]
    desired_replica_count: int

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
        final_filter = ReplicaFilter(ids_in=self._replica_ids)
        if filter:
            final_filter = ReplicaFilter(AND=[final_filter, filter])

        return await resolve_replicas(
            info=info,
            filter=final_filter,
            order_by=order_by,
            before=before,
            after=after,
            first=first,
            last=last,
            limit=limit,
            offset=offset,
        )


@strawberry.type(description="Added in 25.16.0")
class ScalingRule:
    _scaling_rule_ids: strawberry.Private[list[UUID]]

    @strawberry.field
    async def auto_scaling_rules(self, info: Info[StrawberryGQLContext]) -> list[AutoScalingRule]:
        processor = info.context.processors.deployment
        if processor is None:
            raise ModelDeploymentUnavailable(
                "Model Deployment feature is unavailable. Please contact support."
            )

        result = await processor.batch_load_auto_scaling_rules.wait_for_complete(
            BatchLoadAutoScalingRulesAction(auto_scaling_rule_ids=self._scaling_rule_ids)
        )

        return [AutoScalingRule.from_dataclass(rule) for rule in result.data]


@strawberry.type(description="Added in 25.16.0")
class ModelDeploymentMetadata:
    _project_id: strawberry.Private[UUID]
    _domain_name: strawberry.Private[str]
    name: str
    status: DeploymentStatusGQL
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    @strawberry.field
    async def project(self, info: Info[StrawberryGQLContext]) -> Project:
        project_global_id = to_global_id(
            GroupNode, self._project_id, is_target_graphene_object=True
        )
        return Project(id=ID(project_global_id))

    @strawberry.field
    async def domain(self, info: Info[StrawberryGQLContext]) -> Domain:
        domain_global_id = to_global_id(
            DomainNode, self._domain_name, is_target_graphene_object=True
        )
        return Domain(id=ID(domain_global_id))

    @classmethod
    def from_dataclass(cls, data: ModelDeploymentMetadataInfo) -> "ModelDeploymentMetadata":
        return cls(
            name=data.name,
            status=DeploymentStatusGQL(data.status),
            tags=data.tags,
            _project_id=data.project_id,
            _domain_name=data.domain_name,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )


def _convert_gql_revision_ordering_to_repo_ordering(
    order_by: Optional[list[AccessTokenOrderBy]],
) -> AccessTokenOrderingOptions:
    if order_by is None or len(order_by) == 0:
        return AccessTokenOrderingOptions()

    repo_ordering = []
    for order in order_by:
        desc = order.direction == OrderDirection.DESC
        repo_ordering.append((order.field, desc))

    return AccessTokenOrderingOptions(order_by=repo_ordering)


@strawberry.type(description="Added in 25.16.0")
class ModelDeploymentNetworkAccess:
    _access_token_ids: strawberry.Private[Optional[list[UUID]]]
    endpoint_url: Optional[str] = None
    preferred_domain_name: Optional[str] = None
    open_to_public: bool = False

    @strawberry.field
    async def access_tokens(
        self,
        info: Info[StrawberryGQLContext],
        order_by: Optional[list[AccessTokenOrderBy]] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        last: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> AccessTokenConnection:
        """Resolve access tokens using dataloader."""
        repo_ordering = _convert_gql_revision_ordering_to_repo_ordering(order_by)

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
        action_result = await processor.list_access_tokens.wait_for_complete(
            ListAccessTokensAction(
                pagination=pagination_options,
                ordering=repo_ordering,
            )
        )
        edges = []
        tokens = action_result.data
        total_count = action_result.total_count

        for token in tokens:
            edges.append(
                AccessTokenEdge(
                    node=AccessToken.from_dataclass(token),
                    cursor=to_global_id(AccessToken, token.id),
                )
            )

        page_info = build_page_info(edges, total_count, pagination_options)

        return AccessTokenConnection(
            count=total_count, edges=edges, page_info=page_info.to_strawberry_page_info()
        )

    @classmethod
    def from_dataclass(cls, data: DeploymentNetworkSpec) -> "ModelDeploymentNetworkAccess":
        return cls(
            _access_token_ids=data.access_token_ids,
            endpoint_url=data.url,
            preferred_domain_name=data.preferred_domain_name,
            open_to_public=data.open_to_public,
        )


# Main ModelDeployment Type
@strawberry.type(description="Added in 25.16.0")
class ModelDeployment(Node):
    id: NodeID
    metadata: ModelDeploymentMetadata
    network_access: ModelDeploymentNetworkAccess
    revision: Optional[ModelRevision] = None
    default_deployment_strategy: DeploymentStrategyGQL
    _revision_history_ids: strawberry.Private[list[UUID]]
    _replica_state_data: strawberry.Private[ReplicaStateData]
    _created_user_id: strawberry.Private[UUID]
    _scaling_rule_ids: strawberry.Private[list[UUID]]
    _endpoint_id: strawberry.Private[UUID]

    @strawberry.field
    async def created_user(self, info: Info[StrawberryGQLContext]) -> User:
        user_global_id = to_global_id(
            UserNode, self._created_user_id, is_target_graphene_object=True
        )
        return User(id=strawberry.ID(user_global_id))

    @strawberry.field
    async def scaling_rule(self, info: Info[StrawberryGQLContext]) -> ScalingRule:
        return ScalingRule(
            _scaling_rule_ids=self._scaling_rule_ids,
        )

    @strawberry.field
    async def replica_state(self, info: Info[StrawberryGQLContext]) -> ReplicaState:
        return ReplicaState(
            desired_replica_count=self._replica_state_data.desired_replica_count,
            _replica_ids=self._replica_state_data.replica_ids,
        )

    @strawberry.field(description="Added in 25.19.0. Deployment policy configuration.")
    async def deployment_policy(
        self, info: Info[StrawberryGQLContext]
    ) -> Optional[DeploymentPolicyGQL]:
        """Get the deployment policy for this deployment."""
        processor = info.context.processors.deployment
        if processor is None:
            return None

        try:
            result = await processor.get_deployment_policy.wait_for_complete(
                GetDeploymentPolicyAction(endpoint_id=self._endpoint_id)
            )
            return DeploymentPolicyGQL.from_data(result.data)
        except DeploymentPolicyNotFound:
            return None

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
        final_filter = ModelRevisionFilter(ids_in=self._revision_history_ids)
        if filter:
            final_filter = ModelRevisionFilter(AND=[final_filter, filter])

        return await resolve_revisions(
            info=info,
            filter=final_filter,
            order_by=order_by,
            before=before,
            after=after,
            first=first,
            last=last,
            limit=limit,
            offset=offset,
        )

    @classmethod
    async def batch_load_by_ids(
        cls, ctx: StrawberryGQLContext, deployment_ids: Sequence[UUID]
    ) -> list["ModelDeployment"]:
        """Batch load deployments by their IDs."""
        processor = ctx.processors.deployment
        if processor is None:
            raise ModelDeploymentUnavailable(
                "Model Deployment feature is unavailable. Please contact support."
            )

        result = await processor.batch_load_deployments.wait_for_complete(
            BatchLoadDeploymentsAction(deployment_ids=list(deployment_ids))
        )

        deployment_map = {deployment.id: deployment for deployment in result.data}
        model_deployments = []

        for deployment_id in deployment_ids:
            if deployment_id not in deployment_map:
                raise ModelDeploymentNotFound(f"Deployment with ID {deployment_id} not found")
            model_deployments.append(cls.from_dataclass(deployment_map[deployment_id]))

        return model_deployments

    @classmethod
    def from_dataclass(
        cls,
        data: ModelDeploymentData,
    ) -> "ModelDeployment":
        metadata = ModelDeploymentMetadata(
            name=data.metadata.name,
            status=DeploymentStatusGQL(data.metadata.status),
            tags=data.metadata.tags,
            _project_id=data.metadata.project_id,
            _domain_name=data.metadata.domain_name,
            created_at=data.metadata.created_at,
            updated_at=data.metadata.updated_at,
        )

        return cls(
            id=ID(str(data.id)),
            metadata=metadata,
            network_access=ModelDeploymentNetworkAccess.from_dataclass(data.network_access),
            revision=ModelRevision.from_dataclass(data.revision) if data.revision else None,
            default_deployment_strategy=DeploymentStrategyGQL(
                type=DeploymentStrategyTypeGQL(data.default_deployment_strategy)
            ),
            _created_user_id=data.created_user_id,
            _revision_history_ids=data.revision_history_ids,
            _scaling_rule_ids=data.scaling_rule_ids,
            _replica_state_data=data.replica_state,
            _endpoint_id=data.id,
        )


# Filter Types
@strawberry.input(description="Added in 25.16.0")
class DeploymentStatusFilter:
    in_: Optional[list[DeploymentStatusGQL]] = strawberry.field(name="in", default=None)
    equals: Optional[DeploymentStatusGQL] = None


@strawberry.input(description="Added in 25.16.0")
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

    def to_repo_filter(self) -> DeploymentFilterOptions:
        repo_filter = DeploymentFilterOptions()

        repo_filter.name = self.name
        repo_filter.open_to_public = self.open_to_public
        repo_filter.tags = self.tags
        repo_filter.endpoint_url = self.endpoint_url
        repo_filter.id = UUID(self.id) if self.id else None
        if self.status:
            if self.status.in_ is not None:
                repo_filter.status = RepoDeploymentStatusFilter(
                    type=DeploymentStatusFilterType.IN,
                    values=[ModelDeploymentStatus(status) for status in self.status.in_],
                )
            elif self.status.equals is not None:
                repo_filter.status = RepoDeploymentStatusFilter(
                    type=DeploymentStatusFilterType.EQUALS,
                    values=[ModelDeploymentStatus(self.status.equals)],
                )

        # Handle logical operations
        if self.AND:
            repo_filter.AND = [f.to_repo_filter() for f in self.AND]
        if self.OR:
            repo_filter.OR = [f.to_repo_filter() for f in self.OR]
        if self.NOT:
            repo_filter.NOT = [f.to_repo_filter() for f in self.NOT]

        return repo_filter


@strawberry.input(description="Added in 25.16.0")
class DeploymentOrderBy:
    field: DeploymentOrderField
    direction: OrderDirection = OrderDirection.DESC


# Payload Types
@strawberry.type(description="Added in 25.16.0")
class CreateModelDeploymentPayload:
    deployment: ModelDeployment


@strawberry.type(description="Added in 25.16.0")
class UpdateModelDeploymentPayload:
    deployment: ModelDeployment


@strawberry.type(description="Added in 25.16.0")
class DeleteModelDeploymentPayload:
    id: ID


@strawberry.type(description="Added in 25.16.0")
class DeploymentStatusChangedPayload:
    deployment: ModelDeployment


# Input Types
@strawberry.input(description="Added in 25.16.0")
class ModelDeploymentMetadataInput:
    project_id: ID
    domain_name: str
    name: Optional[str] = None
    tags: Optional[list[str]] = None


@strawberry.input(description="Added in 25.16.0")
class ModelDeploymentNetworkAccessInput:
    preferred_domain_name: Optional[str] = None
    open_to_public: bool = False

    def to_network_spec(self) -> DeploymentNetworkSpec:
        return DeploymentNetworkSpec(
            open_to_public=self.open_to_public,
            preferred_domain_name=self.preferred_domain_name,
        )


@strawberry.input(
    name="DeploymentStrategyInput",
    description="Added in 25.19.0. Deployment strategy configuration with discriminator pattern.",
)
class DeploymentStrategyInputGQL:
    """Deployment strategy input with type discriminator and optional config fields.

    The `type` field determines which config field should be provided:
    - ROLLING: requires `rolling_update` config
    - BLUE_GREEN: requires `blue_green` config
    """

    type: DeploymentStrategyTypeGQL
    rollback_on_failure: bool = False
    rolling_update: Optional[RollingUpdateConfigInputGQL] = None
    blue_green: Optional[BlueGreenConfigInputGQL] = None

    def validate(self) -> None:
        """Validate that the appropriate config is provided for the strategy type."""
        if self.type == DeploymentStrategy.ROLLING and not self.rolling_update:
            raise InvalidAPIParameters("rolling_update config required for ROLLING strategy")
        if self.type == DeploymentStrategy.BLUE_GREEN and not self.blue_green:
            raise InvalidAPIParameters("blue_green config required for BLUE_GREEN strategy")

    def to_policy_config(self) -> DeploymentPolicyConfig:
        """Convert to DeploymentPolicyConfig for service layer."""
        self.validate()
        strategy = DeploymentStrategy(self.type.value)
        match strategy:
            case DeploymentStrategy.ROLLING:
                assert self.rolling_update is not None
                return DeploymentPolicyConfig(
                    strategy=strategy,
                    strategy_spec=self.rolling_update.to_spec(),
                    rollback_on_failure=self.rollback_on_failure,
                )
            case DeploymentStrategy.BLUE_GREEN:
                assert self.blue_green is not None
                return DeploymentPolicyConfig(
                    strategy=strategy,
                    strategy_spec=self.blue_green.to_spec(),
                    rollback_on_failure=self.rollback_on_failure,
                )


@strawberry.input(description="Added in 25.16.0")
class CreateModelDeploymentInput:
    metadata: ModelDeploymentMetadataInput
    network_access: ModelDeploymentNetworkAccessInput
    default_deployment_strategy: DeploymentStrategyInputGQL
    desired_replica_count: int
    initial_revision: CreateModelRevisionInput

    def to_creator(self) -> NewDeploymentCreator:
        name = self.metadata.name or f"deployment-{uuid4().hex[:8]}"
        tag = ",".join(self.metadata.tags) if self.metadata.tags else None
        user_data = current_user()
        if user_data is None:
            raise UserNotFound("User not found in context")
        metadata_for_creator = DeploymentMetadata(
            name=name,
            domain=self.metadata.domain_name,
            project=UUID(str(self.metadata.project_id)),
            resource_group=self.initial_revision.resource_config.resource_group.name,
            created_user=user_data.user_id,
            session_owner=user_data.user_id,
            created_at=None,
            revision_history_limit=10,
            tag=tag,
        )
        return NewDeploymentCreator(
            metadata=metadata_for_creator,
            replica_spec=ReplicaSpec(replica_count=self.desired_replica_count),
            network=self.network_access.to_network_spec(),
            model_revision=self.initial_revision.to_model_revision_creator(),
            policy=self.default_deployment_strategy.to_policy_config(),
        )


@strawberry.input(description="Added in 25.16.0")
class UpdateModelDeploymentInput:
    id: ID
    open_to_public: Optional[bool] = None
    tags: Optional[list[str]] = None
    default_deployment_strategy: Optional[DeploymentStrategyInputGQL] = None
    active_revision_id: Optional[ID] = None
    desired_replica_count: Optional[int] = None
    name: Optional[str] = None
    preferred_domain_name: Optional[str] = None

    def to_updater_spec(self) -> NewDeploymentUpdaterSpec:
        strategy_type = None
        if self.default_deployment_strategy is not None:
            strategy_type = DeploymentStrategy(self.default_deployment_strategy.type)
        return NewDeploymentUpdaterSpec(
            open_to_public=OptionalState[bool].from_graphql(self.open_to_public),
            tags=OptionalState[list[str]].from_graphql(self.tags),
            default_deployment_strategy=OptionalState[DeploymentStrategy].from_graphql(
                strategy_type
            ),
            active_revision_id=OptionalState[UUID].from_graphql(UUID(self.active_revision_id)),
            desired_replica_count=OptionalState[int].from_graphql(self.desired_replica_count),
            name=OptionalState[str].from_graphql(self.name),
            preferred_domain_name=TriState[str].from_graphql(self.preferred_domain_name),
        )

    def to_policy_updater_spec(self) -> Optional[DeploymentPolicyUpdaterSpec]:
        """Convert deployment strategy input to policy updater spec.

        Returns None if no deployment_strategy is provided (no policy update).
        """
        if self.default_deployment_strategy is None:
            return None

        # Validate and convert
        policy_config = self.default_deployment_strategy.to_policy_config()
        return DeploymentPolicyUpdaterSpec(
            strategy=OptionalState.update(policy_config.strategy),
            strategy_spec=OptionalState.update(policy_config.strategy_spec),
            rollback_on_failure=OptionalState.update(policy_config.rollback_on_failure),
        )


@strawberry.input(description="Added in 25.16.0")
class DeleteModelDeploymentInput:
    id: ID


ModelDeploymentEdge = Edge[ModelDeployment]


# Connection types for Relay support
@strawberry.type(description="Added in 25.16.0")
class ModelDeploymentConnection(Connection[ModelDeployment]):
    count: int

    def __init__(self, *args, count: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.count = count


def _convert_gql_deployment_ordering_to_repo(
    order_by: Optional[list[DeploymentOrderBy]],
) -> DeploymentOrderingOptions:
    if order_by is None or len(order_by) == 0:
        return DeploymentOrderingOptions()

    repo_ordering = []
    for order in order_by:
        desc = order.direction == OrderDirection.DESC
        repo_ordering.append((order.field, desc))
    return DeploymentOrderingOptions(order_by=repo_ordering)


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
    repo_filter = None
    if filter:
        repo_filter = filter.to_repo_filter()

    repo_ordering = _convert_gql_deployment_ordering_to_repo(order_by)

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
    action_result = await processor.list_deployments.wait_for_complete(
        ListDeploymentsAction(
            pagination=pagination_options, ordering=repo_ordering, filters=repo_filter
        )
    )
    edges = []
    for deployment in action_result.data:
        edges.append(
            ModelDeploymentEdge(
                node=ModelDeployment.from_dataclass(deployment), cursor=str(deployment.id)
            )
        )
    page_info = build_page_info(
        edges=edges,
        total_count=action_result.total_count,
        pagination_options=pagination_options,
    )

    connection = ModelDeploymentConnection(
        count=action_result.total_count,
        edges=edges,
        page_info=page_info.to_strawberry_page_info(),
    )
    return connection


# Resolvers
@strawberry.field(description="Added in 25.16.0")
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


@strawberry.field(description="Added in 25.16.0")
async def deployment(id: ID, info: Info[StrawberryGQLContext]) -> Optional[ModelDeployment]:
    """Get a specific deployment by ID."""
    _, deployment_id = resolve_global_id(id)
    deployment_dataloader = info.context.dataloader_registry.get_loader(
        ModelDeployment.batch_load_by_ids, info.context
    )
    deployment: list[ModelDeployment] = await deployment_dataloader.load(deployment_id)

    return deployment[0]


@strawberry.mutation(description="Added in 25.16.0")
async def create_model_deployment(
    input: CreateModelDeploymentInput, info: Info[StrawberryGQLContext]
) -> "CreateModelDeploymentPayload":
    """Create a new model deployment."""

    processor = info.context.processors.deployment
    if processor is None:
        raise ModelDeploymentUnavailable(
            "Model Deployment feature is unavailable. Please contact support."
        )

    result = await processor.create_deployment.wait_for_complete(
        CreateDeploymentAction(creator=input.to_creator())
    )

    return CreateModelDeploymentPayload(deployment=ModelDeployment.from_dataclass(result.data))


@strawberry.mutation(description="Added in 25.16.0")
async def update_model_deployment(
    input: UpdateModelDeploymentInput, info: Info[StrawberryGQLContext]
) -> UpdateModelDeploymentPayload:
    """Update an existing model deployment."""
    _, deployment_id = resolve_global_id(input.id)
    deployment_processor = info.context.processors.deployment
    if deployment_processor is None:
        raise ModelDeploymentUnavailable(
            "Model Deployment feature is unavailable. Please contact support."
        )
    action_result = await deployment_processor.update_deployment.wait_for_complete(
        UpdateDeploymentAction(
            deployment_id=UUID(deployment_id), updater_spec=input.to_updater_spec()
        )
    )
    return UpdateModelDeploymentPayload(
        deployment=ModelDeployment.from_dataclass(action_result.data)
    )


@strawberry.mutation(description="Added in 25.16.0")
async def delete_model_deployment(
    input: DeleteModelDeploymentInput, info: Info[StrawberryGQLContext]
) -> DeleteModelDeploymentPayload:
    """Delete a model deployment."""
    _, deployment_id = resolve_global_id(input.id)
    deployment_processor = info.context.processors.deployment
    if deployment_processor is None:
        raise ModelDeploymentUnavailable(
            "Model Deployment feature is unavailable. Please contact support."
        )
    _ = await deployment_processor.destroy_deployment.wait_for_complete(
        DestroyDeploymentAction(endpoint_id=UUID(deployment_id))
    )
    return DeleteModelDeploymentPayload(id=input.id)


@strawberry.subscription(description="Added in 25.16.0")
async def deployment_status_changed(
    deployment_id: ID, info: Info[StrawberryGQLContext]
) -> AsyncGenerator[DeploymentStatusChangedPayload, None]:
    """Subscribe to deployment status changes."""
    # Mock implementation
    # In real implementation, this would yield artifacts when status changes
    if False:  # Placeholder to make this a generator
        yield DeploymentStatusChangedPayload(deployment_id=deployment_id)


@strawberry.input(description="Added in 25.16.0")
class SyncReplicaInput:
    model_deployment_id: ID


@strawberry.type(description="Added in 25.16.0")
class SyncReplicaPayload:
    success: bool


@strawberry.mutation(
    description="Added in 25.16.0. Force syncs up-to-date replica information. In normal situations this will be automatically handled by Backend.AI schedulers"
)
async def sync_replicas(
    input: SyncReplicaInput, info: Info[StrawberryGQLContext]
) -> SyncReplicaPayload:
    _, deployment_id = resolve_global_id(input.model_deployment_id)
    deployment_processor = info.context.processors.deployment
    if deployment_processor is None:
        raise ModelDeploymentUnavailable(
            "Model Deployment feature is unavailable. Please contact support."
        )
    await deployment_processor.sync_replicas.wait_for_complete(
        SyncReplicaAction(deployment_id=UUID(deployment_id))
    )
    return SyncReplicaPayload(success=True)
