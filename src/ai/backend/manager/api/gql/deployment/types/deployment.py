"""Deployment GraphQL types."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any, Self
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, NodeID, PageInfo

from ai.backend.common.api_handlers import SENTINEL
from ai.backend.common.data.model_deployment.types import (
    DeploymentStrategy,
    ModelDeploymentStatus,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    AdminSearchRevisionsInput,
    SearchAccessTokensInput,
    SearchAutoScalingRulesInput,
    SearchReplicasInput,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    BlueGreenConfigInput as BlueGreenConfigInputDTO,
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
    RollingUpdateConfigInput as RollingUpdateConfigInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    SyncReplicaInput as SyncReplicaInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    UpdateDeploymentInput as UpdateDeploymentInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    DeploymentNode as DeploymentNodeDTO,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    SyncReplicaPayload as SyncReplicaPayloadDTO,
)
from ai.backend.common.dto.manager.v2.deployment.types import (
    DeploymentOrderField as DTODeploymentOrderField,
)
from ai.backend.common.dto.manager.v2.deployment.types import (
    OrderDirection as DTOOrderDirection,
)
from ai.backend.common.exception import (
    InvalidAPIParameters,
)
from ai.backend.manager.api.gql.base import (
    OrderDirection,
    StringFilter,
    encode_cursor,
    to_global_id,
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
from ai.backend.manager.data.deployment.creator import DeploymentPolicyConfig
from ai.backend.manager.data.deployment.types import (
    AccessTokenSearchScope,
    AutoScalingRuleSearchScope,
    DeploymentNetworkSpec,
    DeploymentOrderField,
    ModelDeploymentData,
    ModelDeploymentMetadataInfo,
    ReplicaSearchScope,
    RevisionSearchScope,
)

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
            scope=ReplicaSearchScope(deployment_id=self._deployment_id),
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
        nodes = [ModelReplica.from_node(item) for item in payload.items]
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
            scope=AutoScalingRuleSearchScope(deployment_id=self._deployment_id),
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
        nodes = [AutoScalingRule.from_node(item) for item in payload.items]
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
    endpoint_url: str | None = None
    preferred_domain_name: str | None = None
    open_to_public: bool = False

    @strawberry.field
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
        """Resolve access tokens for this deployment."""
        pydantic_filter = filter.to_pydantic() if filter else None
        pydantic_order = [o.to_pydantic() for o in order_by] if order_by else None
        payload = await info.context.adapters.deployment.search_access_tokens(
            scope=AccessTokenSearchScope(deployment_id=self._deployment_id),
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
        nodes = [AccessToken.from_node(item) for item in payload.items]
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
class ModelDeployment(PydanticNodeMixin):
    """
    Added in 25.19.0.

    Represents a model deployment in Backend.AI. A deployment is a long-running
    inference service that exposes a trained model via HTTP endpoints.

    Deployments manage the lifecycle of model replicas, handle traffic routing,
    and provide auto-scaling capabilities based on configured rules.
    """

    id: NodeID[str]
    metadata: ModelDeploymentMetadata
    network_access: ModelDeploymentNetworkAccess
    revision: ModelRevision | None = None
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

    @strawberry.field(description="Added in 25.19.0. Deployment policy configuration.")  # type: ignore[misc]
    async def deployment_policy(
        self, info: Info[StrawberryGQLContext]
    ) -> DeploymentPolicyGQL | None:
        """Get the deployment policy for this deployment."""
        policy_data = await info.context.data_loaders.deployment_policy_by_endpoint_loader.load(
            self._deployment_id
        )
        if policy_data is None:
            return None
        return DeploymentPolicyGQL.from_data(policy_data)

    @strawberry.field
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
            scope=RevisionSearchScope(deployment_id=self._deployment_id),
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
        nodes = [ModelRevision.from_node(item) for item in payload.items]
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
        return [cls.from_dataclass(data) if data is not None else None for data in results]

    @classmethod
    def from_dataclass(
        cls,
        data: ModelDeploymentData,
    ) -> Self:
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

    @classmethod
    def from_node(cls, node: DeploymentNodeDTO) -> Self:
        metadata = ModelDeploymentMetadata(
            name=node.basic.name,
            status=DeploymentStatusGQL(node.basic.status),
            tags=node.basic.tags,
            _project_id=node.basic.project_id,
            _domain_name=node.basic.domain_name,
            created_at=node.created_at,
            updated_at=node.updated_at,
        )
        return cls(
            id=ID(str(node.id)),
            metadata=metadata,
            network_access=ModelDeploymentNetworkAccess(
                _deployment_id=node.id,
                endpoint_url=node.network.url,
                preferred_domain_name=node.network.preferred_domain_name,
                open_to_public=node.network.open_to_public,
            ),
            revision=ModelRevision.from_node(node.current_revision)
            if node.current_revision
            else None,
            default_deployment_strategy=DeploymentStrategyGQL(
                type=DeploymentStrategyTypeGQL(node.default_deployment_strategy)
            ),
            replica_state=ReplicaState(
                desired_replica_count=node.replica_state.desired_replica_count,
                _deployment_id=node.id,
            ),
            _created_user_id=node.basic.created_user_id,
            _deployment_id=node.id,
        )


# Filter Types
@strawberry.experimental.pydantic.input(
    model=DeploymentStatusFilterDTO,
    description="Added in 25.19.0",
)
class DeploymentStatusFilter:
    in_: list[DeploymentStatusGQL] | None = strawberry.field(name="in", default=None)
    equals: DeploymentStatusGQL | None = None

    def to_pydantic(self) -> DeploymentStatusFilterDTO:
        return DeploymentStatusFilterDTO(
            equals=self.equals.value if self.equals else None,
            in_=[s.value for s in self.in_] if self.in_ else None,
        )


@strawberry.experimental.pydantic.input(
    model=DeploymentFilterDTO,
    description="Added in 25.19.0",
)
class DeploymentFilter:
    name: StringFilter | None = None
    status: DeploymentStatusFilter | None = None
    open_to_public: bool | None = None
    tags: StringFilter | None = None
    endpoint_url: StringFilter | None = None

    AND: list[DeploymentFilter] | None = None
    OR: list[DeploymentFilter] | None = None
    NOT: list[DeploymentFilter] | None = None

    def to_pydantic(self) -> DeploymentFilterDTO:
        return DeploymentFilterDTO(
            name=self.name.to_pydantic() if self.name else None,
            status=DeploymentStatusFilterDTO(
                equals=self.status.equals.value if self.status.equals else None,
                in_=[s.value for s in self.status.in_] if self.status.in_ else None,
            )
            if self.status
            else None,
            open_to_public=self.open_to_public,
            tags=self.tags.to_pydantic() if self.tags else None,
            endpoint_url=self.endpoint_url.to_pydantic() if self.endpoint_url else None,
            AND=[f.to_pydantic() for f in self.AND] if self.AND else None,
            OR=[f.to_pydantic() for f in self.OR] if self.OR else None,
            NOT=[f.to_pydantic() for f in self.NOT] if self.NOT else None,
        )


@strawberry.experimental.pydantic.input(
    model=DeploymentOrderDTO,
    description="Added in 25.19.0",
)
class DeploymentOrderBy:
    field: DeploymentOrderField
    direction: OrderDirection = OrderDirection.DESC

    def to_pydantic(self) -> DeploymentOrderDTO:
        return DeploymentOrderDTO(
            field=DTODeploymentOrderField(self.field.value.lower()),
            direction=DTOOrderDirection(self.direction.value.lower()),
        )


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
@strawberry.experimental.pydantic.input(
    model=ModelDeploymentMetadataInputDTO,
    description="Added in 25.19.0",
)
class ModelDeploymentMetadataInput:
    project_id: ID
    domain_name: str
    name: str | None = None
    tags: list[str] | None = None

    def to_pydantic(self) -> ModelDeploymentMetadataInputDTO:
        return ModelDeploymentMetadataInputDTO(
            project_id=UUID(str(self.project_id)),
            domain_name=self.domain_name,
            name=self.name,
            tags=self.tags,
        )


@strawberry.experimental.pydantic.input(
    model=ModelDeploymentNetworkAccessInputDTO,
    description="Added in 25.19.0",
)
class ModelDeploymentNetworkAccessInput:
    preferred_domain_name: str | None = None
    open_to_public: bool = False

    def to_network_spec(self) -> DeploymentNetworkSpec:
        return DeploymentNetworkSpec(
            open_to_public=self.open_to_public,
            preferred_domain_name=self.preferred_domain_name,
        )

    def to_pydantic(self) -> ModelDeploymentNetworkAccessInputDTO:
        return ModelDeploymentNetworkAccessInputDTO(
            preferred_domain_name=self.preferred_domain_name,
            open_to_public=self.open_to_public,
        )


@strawberry.experimental.pydantic.input(
    model=DeploymentStrategyInputDTO,
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
    rolling_update: RollingUpdateConfigInputGQL | None = None
    blue_green: BlueGreenConfigInputGQL | None = None

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
                if self.rolling_update is None:
                    raise InvalidAPIParameters("rolling_update config required but not provided")
                return DeploymentPolicyConfig(
                    strategy=strategy,
                    strategy_spec=self.rolling_update.to_spec(),
                    rollback_on_failure=self.rollback_on_failure,
                )
            case DeploymentStrategy.BLUE_GREEN:
                if self.blue_green is None:
                    raise InvalidAPIParameters("blue_green config required but not provided")
                return DeploymentPolicyConfig(
                    strategy=strategy,
                    strategy_spec=self.blue_green.to_spec(),
                    rollback_on_failure=self.rollback_on_failure,
                )

    def to_pydantic(self) -> DeploymentStrategyInputDTO:
        return DeploymentStrategyInputDTO(
            type=DeploymentStrategy(self.type.value),
            rollback_on_failure=self.rollback_on_failure,
            rolling_update=self.rolling_update.to_pydantic() if self.rolling_update else None,
            blue_green=self.blue_green.to_pydantic() if self.blue_green else None,
        )


@strawberry.experimental.pydantic.input(
    model=CreateDeploymentInputDTO,
    description="Added in 25.19.0",
)
class CreateDeploymentInput:
    metadata: ModelDeploymentMetadataInput
    network_access: ModelDeploymentNetworkAccessInput
    default_deployment_strategy: DeploymentStrategyInputGQL
    desired_replica_count: int
    initial_revision: CreateRevisionInput

    def to_pydantic(self) -> CreateDeploymentInputDTO:
        rolling_update_dto: RollingUpdateConfigInputDTO | None = None
        if self.default_deployment_strategy.rolling_update is not None:
            rolling_update_dto = RollingUpdateConfigInputDTO(
                max_surge=self.default_deployment_strategy.rolling_update.max_surge,
                max_unavailable=self.default_deployment_strategy.rolling_update.max_unavailable,
            )
        blue_green_dto: BlueGreenConfigInputDTO | None = None
        if self.default_deployment_strategy.blue_green is not None:
            blue_green_dto = BlueGreenConfigInputDTO(
                auto_promote=self.default_deployment_strategy.blue_green.auto_promote,
                promote_delay_seconds=self.default_deployment_strategy.blue_green.promote_delay_seconds,
            )
        revision_dto = self.initial_revision.to_pydantic()
        return CreateDeploymentInputDTO(
            project_id=UUID(str(self.metadata.project_id)),
            domain_name=self.metadata.domain_name,
            name=self.metadata.name,
            tags=self.metadata.tags,
            open_to_public=self.network_access.open_to_public,
            preferred_domain_name=self.network_access.preferred_domain_name,
            strategy=DeploymentStrategy(self.default_deployment_strategy.type.value),
            rollback_on_failure=self.default_deployment_strategy.rollback_on_failure,
            desired_replica_count=self.desired_replica_count,
            initial_revision=revision_dto,
            rolling_update=rolling_update_dto,
            blue_green=blue_green_dto,
        )


@strawberry.experimental.pydantic.input(
    model=UpdateDeploymentInputDTO,
    description="Added in 25.19.0",
)
class UpdateDeploymentInput:
    id: ID
    open_to_public: bool | None = None
    tags: list[str] | None = None
    default_deployment_strategy: DeploymentStrategyInputGQL | None = None
    active_revision_id: ID | None = None
    desired_replica_count: int | None = None
    name: str | None = None
    preferred_domain_name: str | None = None

    def to_pydantic(self) -> UpdateDeploymentInputDTO:
        return UpdateDeploymentInputDTO(
            name=self.name,
            desired_replicas=self.desired_replica_count,
            tags=SENTINEL if self.tags is None else self.tags,
        )


@strawberry.experimental.pydantic.input(
    model=DeleteDeploymentInputDTO,
    description="Added in 25.19.0",
)
class DeleteDeploymentInput:
    id: ID


ModelDeploymentEdge = Edge[ModelDeployment]


# Connection types for Relay support
@strawberry.type(description="Added in 25.19.0")
class ModelDeploymentConnection(Connection[ModelDeployment]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# Sync replica types
@strawberry.experimental.pydantic.input(
    model=SyncReplicaInputDTO,
    description="Added in 25.19.0",
)
class SyncReplicaInput:
    model_deployment_id: ID


@strawberry.experimental.pydantic.type(
    model=SyncReplicaPayloadDTO,
    description="Added in 25.19.0",
    all_fields=True,
)
class SyncReplicaPayload:
    """Payload for replica sync mutation result."""
