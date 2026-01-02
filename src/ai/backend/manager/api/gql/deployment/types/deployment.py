"""Deployment GraphQL types."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Optional, override
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
)
from ai.backend.manager.api.gql.base import (
    OrderDirection,
    StringFilter,
    to_global_id,
)
from ai.backend.manager.api.gql.deployment.types.access_token import (
    AccessTokenConnection,
    AccessTokenFilter,
    AccessTokenOrderBy,
)
from ai.backend.manager.api.gql.deployment.types.auto_scaling import (
    AutoScalingRuleConnection,
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
    ModelReplicaConnection,
    ReplicaFilter,
    ReplicaOrderBy,
)
from ai.backend.manager.api.gql.deployment.types.revision import (
    CreateRevisionInput,
    ModelRevision,
    ModelRevisionConnection,
    ModelRevisionFilter,
    ModelRevisionOrderBy,
)
from ai.backend.manager.api.gql.domain import Domain
from ai.backend.manager.api.gql.project import Project
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext
from ai.backend.manager.api.gql.user import User
from ai.backend.manager.data.deployment.creator import DeploymentPolicyConfig, NewDeploymentCreator
from ai.backend.manager.data.deployment.types import (
    DeploymentMetadata,
    DeploymentNetworkSpec,
    DeploymentOrderField,
    ModelDeploymentData,
    ModelDeploymentMetadataInfo,
    ReplicaSpec,
)
from ai.backend.manager.errors.service import DeploymentPolicyNotFound
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.gql_models.domain import DomainNode
from ai.backend.manager.models.gql_models.group import GroupNode
from ai.backend.manager.models.gql_models.user import UserNode
from ai.backend.manager.repositories.base import (
    QueryCondition,
    QueryOrder,
    Updater,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.deployment.options import (
    AccessTokenConditions,
    AutoScalingRuleConditions,
    DeploymentConditions,
    DeploymentOrders,
    RevisionConditions,
    RouteConditions,
)
from ai.backend.manager.repositories.deployment.updaters import (
    DeploymentMetadataUpdaterSpec,
    DeploymentNetworkSpecUpdaterSpec,
    DeploymentPolicyUpdaterSpec,
    DeploymentUpdaterSpec,
    ReplicaSpecUpdaterSpec,
    RevisionStateUpdaterSpec,
)
from ai.backend.manager.services.deployment.actions.deployment_policy import (
    GetDeploymentPolicyAction,
)
from ai.backend.manager.types import OptionalState, TriState

DeploymentStatusGQL: type[ModelDeploymentStatus] = strawberry.enum(
    ModelDeploymentStatus,
    name="DeploymentStatus",
    description="Added in 25.19.0. This enum represents the deployment status of a model deployment, indicating its current state.",
)


@strawberry.type
class DeploymentStrategyGQL:
    """
    Added in 25.19.0.

    Represents the deployment strategy configuration that determines how
    updates are rolled out to replicas (e.g., rolling update, blue-green).
    """

    type: DeploymentStrategyTypeGQL


@strawberry.type
class ReplicaState:
    """
    Added in 25.19.0.

    Represents the current replica state of a deployment, including the desired
    replica count and access to the list of active replicas.
    """

    _deployment_id: strawberry.Private[UUID]
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
        from ai.backend.manager.api.gql.deployment.fetcher.replica import fetch_replicas

        return await fetch_replicas(
            info=info,
            filter=filter,
            order_by=order_by,
            before=before,
            after=after,
            first=first,
            last=last,
            limit=limit,
            offset=offset,
            base_conditions=[RouteConditions.by_endpoint_id(self._deployment_id)],
        )


@strawberry.type
class ScalingRule:
    """
    Added in 25.19.0.

    Provides access to auto-scaling rules configured for a deployment.
    Auto-scaling rules define conditions for automatically adjusting
    the number of replicas based on metrics.
    """

    _deployment_id: strawberry.Private[UUID]

    @strawberry.field
    async def auto_scaling_rules(
        self,
        info: Info[StrawberryGQLContext],
        filter: Optional[AutoScalingRuleFilter] = None,
        order_by: Optional[list[AutoScalingRuleOrderBy]] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        last: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> AutoScalingRuleConnection:
        from ai.backend.manager.api.gql.deployment.fetcher.auto_scaling import (
            fetch_auto_scaling_rules,
        )

        return await fetch_auto_scaling_rules(
            info=info,
            filter=filter,
            order_by=order_by,
            before=before,
            after=after,
            first=first,
            last=last,
            limit=limit,
            offset=offset,
            base_conditions=[AutoScalingRuleConditions.by_deployment_id(self._deployment_id)],
        )


@strawberry.type
class ModelDeploymentMetadata:
    """
    Added in 25.19.0.

    Contains metadata information for a model deployment including its name,
    status, tags, and timestamps. Also provides access to the associated
    project and domain.
    """

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
    def from_dataclass(cls, data: ModelDeploymentMetadataInfo) -> ModelDeploymentMetadata:
        return cls(
            name=data.name,
            status=DeploymentStatusGQL(data.status),
            tags=data.tags,
            _project_id=data.project_id,
            _domain_name=data.domain_name,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )


@strawberry.type
class ModelDeploymentNetworkAccess:
    """
    Added in 25.19.0.

    Provides network access configuration for a model deployment, including
    the endpoint URL, preferred domain name, and public access settings.
    Also manages access tokens for authentication.
    """

    _deployment_id: strawberry.Private[UUID]
    endpoint_url: Optional[str] = None
    preferred_domain_name: Optional[str] = None
    open_to_public: bool = False

    @strawberry.field
    async def access_tokens(
        self,
        info: Info[StrawberryGQLContext],
        filter: Optional[AccessTokenFilter] = None,
        order_by: Optional[list[AccessTokenOrderBy]] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        last: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> AccessTokenConnection:
        """Resolve access tokens for this deployment."""
        from ai.backend.manager.api.gql.deployment.fetcher.access_token import (
            fetch_access_tokens,
        )

        return await fetch_access_tokens(
            info=info,
            filter=filter,
            order_by=order_by,
            before=before,
            after=after,
            first=first,
            last=last,
            limit=limit,
            offset=offset,
            base_conditions=[AccessTokenConditions.by_endpoint_id(self._deployment_id)],
        )

    @classmethod
    def from_dataclass(
        cls, data: DeploymentNetworkSpec, deployment_id: UUID
    ) -> ModelDeploymentNetworkAccess:
        return cls(
            _deployment_id=deployment_id,
            endpoint_url=data.url,
            preferred_domain_name=data.preferred_domain_name,
            open_to_public=data.open_to_public,
        )


# Main ModelDeployment Type
@strawberry.type
class ModelDeployment(Node):
    """
    Added in 25.19.0.

    Represents a model deployment in Backend.AI. A deployment is a long-running
    inference service that exposes a trained model via HTTP endpoints.

    Deployments manage the lifecycle of model replicas, handle traffic routing,
    and provide auto-scaling capabilities based on configured rules.
    """

    id: NodeID
    metadata: ModelDeploymentMetadata
    network_access: ModelDeploymentNetworkAccess
    revision: Optional[ModelRevision] = None
    default_deployment_strategy: DeploymentStrategyGQL
    replica_state: ReplicaState
    _created_user_id: strawberry.Private[UUID]
    _deployment_id: strawberry.Private[UUID]

    @strawberry.field
    async def created_user(self, info: Info[StrawberryGQLContext]) -> User:
        user_global_id = to_global_id(
            UserNode, self._created_user_id, is_target_graphene_object=True
        )
        return User(id=strawberry.ID(user_global_id))

    @strawberry.field
    async def scaling_rule(self, info: Info[StrawberryGQLContext]) -> ScalingRule:
        return ScalingRule(
            _deployment_id=self._deployment_id,
        )

    @strawberry.field(description="Added in 25.19.0. Deployment policy configuration.")
    async def deployment_policy(
        self, info: Info[StrawberryGQLContext]
    ) -> Optional[DeploymentPolicyGQL]:
        """Get the deployment policy for this deployment."""
        processor = info.context.processors.deployment

        try:
            result = await processor.get_deployment_policy.wait_for_complete(
                GetDeploymentPolicyAction(endpoint_id=self._deployment_id)
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
        from ai.backend.manager.api.gql.deployment.fetcher.revision import fetch_revisions

        return await fetch_revisions(
            info=info,
            filter=filter,
            order_by=order_by,
            before=before,
            after=after,
            first=first,
            last=last,
            limit=limit,
            offset=offset,
            base_conditions=[RevisionConditions.by_deployment_id(self._deployment_id)],
        )

    @classmethod
    def from_dataclass(
        cls,
        data: ModelDeploymentData,
    ) -> ModelDeployment:
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
            network_access=ModelDeploymentNetworkAccess.from_dataclass(
                data.network_access, deployment_id=data.id
            ),
            revision=ModelRevision.from_dataclass(data.revision) if data.revision else None,
            default_deployment_strategy=DeploymentStrategyGQL(
                type=DeploymentStrategyTypeGQL(data.default_deployment_strategy)
            ),
            replica_state=ReplicaState(
                desired_replica_count=data.replica_state.desired_replica_count,
                _deployment_id=data.id,
            ),
            _created_user_id=data.created_user_id,
            _deployment_id=data.id,
        )


# Filter Types
@strawberry.input(description="Added in 25.19.0")
class DeploymentStatusFilter:
    in_: Optional[list[DeploymentStatusGQL]] = strawberry.field(name="in", default=None)
    equals: Optional[DeploymentStatusGQL] = None


@strawberry.input(description="Added in 25.19.0")
class DeploymentFilter(GQLFilter):
    name: Optional[StringFilter] = None
    status: Optional[DeploymentStatusFilter] = None
    open_to_public: Optional[bool] = None
    tags: Optional[StringFilter] = None
    endpoint_url: Optional[StringFilter] = None
    ids_in: strawberry.Private[Optional[Sequence[UUID]]] = None

    AND: Optional[list["DeploymentFilter"]] = None
    OR: Optional[list["DeploymentFilter"]] = None
    NOT: Optional[list["DeploymentFilter"]] = None

    @override
    def build_conditions(self) -> list[QueryCondition]:
        """Build query conditions from this filter.

        Returns a list of QueryCondition callables that can be applied to SQLAlchemy queries.
        """
        field_conditions: list[QueryCondition] = []

        # Apply name filter
        if self.name:
            name_condition = self.name.build_query_condition(
                contains_factory=DeploymentConditions.by_name_contains,
                equals_factory=DeploymentConditions.by_name_equals,
            )
            if name_condition:
                field_conditions.append(name_condition)

        # Apply status filter
        if self.status:
            if self.status.in_ is not None:
                statuses = [ModelDeploymentStatus(s) for s in self.status.in_]
                field_conditions.append(DeploymentConditions.by_status_in(statuses))
            elif self.status.equals is not None:
                field_conditions.append(
                    DeploymentConditions.by_status_equals(ModelDeploymentStatus(self.status.equals))
                )

        # Apply open_to_public filter
        if self.open_to_public is not None:
            field_conditions.append(DeploymentConditions.by_open_to_public(self.open_to_public))

        # Apply tags filter
        if self.tags:
            tags_condition = self.tags.build_query_condition(
                contains_factory=DeploymentConditions.by_tag_contains,
                equals_factory=DeploymentConditions.by_tag_equals,
            )
            if tags_condition:
                field_conditions.append(tags_condition)

        # Apply endpoint_url filter
        if self.endpoint_url:
            url_condition = self.endpoint_url.build_query_condition(
                contains_factory=DeploymentConditions.by_url_contains,
                equals_factory=DeploymentConditions.by_url_equals,
            )
            if url_condition:
                field_conditions.append(url_condition)

        # Apply ids_in filter (internal use)
        if self.ids_in:
            field_conditions.append(DeploymentConditions.by_ids(self.ids_in))

        # Handle AND logical operator - these are implicitly ANDed with field conditions
        if self.AND:
            for sub_filter in self.AND:
                field_conditions.extend(sub_filter.build_conditions())

        # Handle OR logical operator
        if self.OR:
            or_sub_conditions: list[QueryCondition] = []
            for sub_filter in self.OR:
                or_sub_conditions.extend(sub_filter.build_conditions())
            if or_sub_conditions:
                field_conditions.append(combine_conditions_or(or_sub_conditions))

        # Handle NOT logical operator
        if self.NOT:
            not_sub_conditions: list[QueryCondition] = []
            for sub_filter in self.NOT:
                not_sub_conditions.extend(sub_filter.build_conditions())
            if not_sub_conditions:
                field_conditions.append(negate_conditions(not_sub_conditions))

        return field_conditions


@strawberry.input(description="Added in 25.19.0")
class DeploymentOrderBy(GQLOrderBy):
    field: DeploymentOrderField
    direction: OrderDirection = OrderDirection.DESC

    @override
    def to_query_order(self) -> QueryOrder:
        """Convert to repository QueryOrder."""
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case DeploymentOrderField.NAME:
                return DeploymentOrders.name(ascending)
            case DeploymentOrderField.CREATED_AT:
                return DeploymentOrders.created_at(ascending)


# Payload Types
@strawberry.type(description="Added in 25.19.0")
class CreateDeploymentPayload:
    deployment: ModelDeployment


@strawberry.type(description="Added in 25.19.0")
class UpdateDeploymentPayload:
    deployment: ModelDeployment


@strawberry.type(description="Added in 25.19.0")
class DeleteDeploymentPayload:
    id: ID


@strawberry.type(description="Added in 25.19.0")
class DeploymentStatusChangedPayload:
    deployment: ModelDeployment


# Input Types
@strawberry.input(description="Added in 25.19.0")
class ModelDeploymentMetadataInput:
    project_id: ID
    domain_name: str
    name: Optional[str] = None
    tags: Optional[list[str]] = None


@strawberry.input(description="Added in 25.19.0")
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


@strawberry.input(description="Added in 25.19.0")
class CreateDeploymentInput:
    metadata: ModelDeploymentMetadataInput
    network_access: ModelDeploymentNetworkAccessInput
    default_deployment_strategy: DeploymentStrategyInputGQL
    desired_replica_count: int
    initial_revision: CreateRevisionInput

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


@strawberry.input(description="Added in 25.19.0")
class UpdateDeploymentInput:
    id: ID
    open_to_public: Optional[bool] = None
    tags: Optional[list[str]] = None
    default_deployment_strategy: Optional[DeploymentStrategyInputGQL] = None
    active_revision_id: Optional[ID] = None
    desired_replica_count: Optional[int] = None
    name: Optional[str] = None
    preferred_domain_name: Optional[str] = None

    def to_updater(self, deployment_id: UUID) -> Updater[EndpointRow]:
        """Convert input to deployment updater."""
        # Build metadata sub-spec if any metadata fields are provided
        metadata_spec: DeploymentMetadataUpdaterSpec | None = None
        if self.name is not None or self.tags is not None:
            # Convert tags list to comma-separated string for tag column
            tag_str: str | None = None
            if self.tags is not None:
                tag_str = ",".join(self.tags)
            metadata_spec = DeploymentMetadataUpdaterSpec(
                name=OptionalState[str].from_graphql(self.name),
                tag=TriState[str].from_graphql(tag_str),
            )

        # Build replica spec sub-spec if any replica fields are provided
        replica_spec: ReplicaSpecUpdaterSpec | None = None
        if self.desired_replica_count is not None:
            replica_spec = ReplicaSpecUpdaterSpec(
                desired_replica_count=OptionalState[int].from_graphql(self.desired_replica_count),
            )

        # Build network sub-spec if any network fields are provided
        network_spec: DeploymentNetworkSpecUpdaterSpec | None = None
        if self.open_to_public is not None:
            network_spec = DeploymentNetworkSpecUpdaterSpec(
                open_to_public=OptionalState[bool].from_graphql(self.open_to_public),
            )

        # Build revision state sub-spec if any revision fields are provided
        revision_state_spec: RevisionStateUpdaterSpec | None = None
        if self.active_revision_id is not None:
            active_revision_uuid = UUID(self.active_revision_id)
            revision_state_spec = RevisionStateUpdaterSpec(
                current_revision=TriState[UUID].from_graphql(active_revision_uuid),
            )

        spec = DeploymentUpdaterSpec(
            metadata=metadata_spec,
            replica_spec=replica_spec,
            network=network_spec,
            revision_state=revision_state_spec,
        )
        return Updater(spec=spec, pk_value=deployment_id)

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


@strawberry.input(description="Added in 25.19.0")
class DeleteDeploymentInput:
    id: ID


ModelDeploymentEdge = Edge[ModelDeployment]


# Connection types for Relay support
@strawberry.type(description="Added in 25.19.0")
class ModelDeploymentConnection(Connection[ModelDeployment]):
    count: int

    def __init__(self, *args, count: int, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# Sync replica types
@strawberry.input(description="Added in 25.19.0")
class SyncReplicaInput:
    model_deployment_id: ID


@strawberry.type(description="Added in 25.19.0")
class SyncReplicaPayload:
    success: bool
