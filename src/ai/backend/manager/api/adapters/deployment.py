"""Deployment adapter bridging DTOs and Processors."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.api_handlers import Sentinel
from ai.backend.common.data.model_deployment.types import (
    DeploymentStrategy,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    AddRevisionInput,
    AdminSearchDeploymentsInput,
    AdminSearchRevisionsInput,
    CreateAccessTokenInput,
    CreateAutoScalingRuleInput,
    CreateDeploymentInput,
    DeleteAutoScalingRuleInput,
    DeleteDeploymentInput,
    DeploymentOrder,
    RevisionOrder,
    RouteOrder,
    SearchAccessTokensInput,
    SearchAutoScalingRulesInput,
    SearchDeploymentPoliciesInput,
    SearchRoutesInput,
    UpdateAutoScalingRuleInput,
    UpdateDeploymentInput,
    UpsertDeploymentPolicyInput,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    AccessTokenNode,
    AddRevisionPayload,
    AdminSearchDeploymentsPayload,
    AdminSearchRevisionsPayload,
    AutoScalingRuleNode,
    CreateAccessTokenPayload,
    CreateAutoScalingRulePayload,
    CreateDeploymentPayload,
    DeleteAutoScalingRulePayload,
    DeleteDeploymentPayload,
    DeploymentNode,
    DeploymentPolicyNode,
    ExtraVFolderMountNode,
    GetAutoScalingRulePayload,
    GetDeploymentPolicyPayload,
    RevisionNode,
    RouteNode,
    SearchAccessTokensPayload,
    SearchAutoScalingRulesPayload,
    SearchDeploymentPoliciesPayload,
    SearchRoutesPayload,
    UpdateAutoScalingRulePayload,
    UpdateDeploymentPayload,
    UpsertDeploymentPolicyPayload,
)
from ai.backend.common.dto.manager.v2.deployment.types import (
    BlueGreenConfigInfo,
    DeploymentBasicInfo,
    DeploymentOrderField,
    DeploymentPolicyInfo,
    DeploymentRevisionInfo,
    NetworkConfigInfo,
    OrderDirection,
    ReplicaStateInfo,
    RevisionOrderField,
    RollingUpdateConfigInfo,
    RouteOrderField,
)
from ai.backend.manager.data.deployment.access_token import ModelDeploymentAccessTokenCreator
from ai.backend.manager.data.deployment.creator import (
    DeploymentPolicyConfig,
    ModelRevisionCreator,
    NewDeploymentCreator,
    VFolderMountsCreator,
)
from ai.backend.manager.data.deployment.scale import ModelDeploymentAutoScalingRuleCreator
from ai.backend.manager.data.deployment.scale_modifier import (
    ModelDeploymentAutoScalingRuleModifier,
)
from ai.backend.manager.data.deployment.types import (
    DeploymentMetadata,
    DeploymentNetworkSpec,
    DeploymentPolicyData,
    ExecutionSpec,
    ModelDeploymentAccessTokenData,
    ModelDeploymentAutoScalingRuleData,
    ModelDeploymentData,
    ModelRevisionData,
    MountInfo,
    ReplicaSpec,
    ResourceSpec,
    RouteInfo,
)
from ai.backend.manager.data.deployment.types import (
    RouteStatus as ManagerRouteStatus,
)
from ai.backend.manager.data.deployment.types import (
    RouteTrafficStatus as ManagerRouteTrafficStatus,
)
from ai.backend.manager.data.deployment.upserter import DeploymentPolicyUpserter
from ai.backend.manager.models.deployment_policy import BlueGreenSpec, RollingUpdateSpec
from ai.backend.manager.models.deployment_policy.conditions import DeploymentPolicyConditions
from ai.backend.manager.models.deployment_revision.conditions import RevisionConditions
from ai.backend.manager.models.deployment_revision.orders import RevisionOrders
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.endpoint.conditions import (
    AccessTokenConditions,
    AutoScalingRuleConditions,
    DeploymentConditions,
)
from ai.backend.manager.models.endpoint.orders import (
    AccessTokenOrders,
    AutoScalingRuleOrders,
    DeploymentOrders,
)
from ai.backend.manager.models.routing.conditions import RouteConditions
from ai.backend.manager.models.routing.orders import RouteOrders
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
    Updater,
)
from ai.backend.manager.repositories.deployment.updaters import (
    DeploymentMetadataUpdaterSpec,
    DeploymentUpdaterSpec,
    ReplicaSpecUpdaterSpec,
)
from ai.backend.manager.services.deployment.actions.access_token.create_access_token import (
    CreateAccessTokenAction,
)
from ai.backend.manager.services.deployment.actions.access_token.search_access_tokens import (
    SearchAccessTokensAction,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.create_auto_scaling_rule import (
    CreateAutoScalingRuleAction,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.delete_auto_scaling_rule import (
    DeleteAutoScalingRuleAction,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.get_auto_scaling_rule import (
    GetAutoScalingRuleAction,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.search_auto_scaling_rules import (
    SearchAutoScalingRulesAction,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.update_auto_scaling_rule import (
    UpdateAutoScalingRuleAction,
)
from ai.backend.manager.services.deployment.actions.create_deployment import CreateDeploymentAction
from ai.backend.manager.services.deployment.actions.deployment_policy.get_deployment_policy import (
    GetDeploymentPolicyAction,
)
from ai.backend.manager.services.deployment.actions.deployment_policy.search_deployment_policies import (
    SearchDeploymentPoliciesAction,
)
from ai.backend.manager.services.deployment.actions.deployment_policy.upsert_deployment_policy import (
    UpsertDeploymentPolicyAction,
)
from ai.backend.manager.services.deployment.actions.destroy_deployment import (
    DestroyDeploymentAction,
)
from ai.backend.manager.services.deployment.actions.get_deployment_by_id import (
    GetDeploymentByIdAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.add_model_revision import (
    AddModelRevisionAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.get_revision_by_id import (
    GetRevisionByIdAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.search_revisions import (
    SearchRevisionsAction,
)
from ai.backend.manager.services.deployment.actions.route.search_routes import SearchRoutesAction
from ai.backend.manager.services.deployment.actions.route.update_route_traffic_status import (
    UpdateRouteTrafficStatusAction,
)
from ai.backend.manager.services.deployment.actions.search_deployments import (
    SearchDeploymentsAction,
)
from ai.backend.manager.services.deployment.actions.update_deployment import UpdateDeploymentAction
from ai.backend.manager.types import OptionalState, TriState

from .base import BaseAdapter

DEFAULT_PAGINATION_LIMIT = 10


class DeploymentAdapter(BaseAdapter):
    """Adapter for deployment domain operations."""

    # ------------------------------------------------------------------
    # Core deployment operations
    # ------------------------------------------------------------------

    async def create(
        self,
        input: CreateDeploymentInput,
        created_user_id: UUID,
    ) -> CreateDeploymentPayload:
        """Create a new deployment."""
        mounts_creator = VFolderMountsCreator(
            model_vfolder_id=input.initial_revision.model_vfolder_id,
            model_definition_path=input.initial_revision.model_definition_path,
            model_mount_destination=input.initial_revision.model_mount_destination,
            extra_mounts=[
                MountInfo(
                    vfolder_id=m.vfolder_id,
                    kernel_path=None,
                )
                for m in (input.initial_revision.extra_mounts or [])
            ],
        )
        model_revision_creator = ModelRevisionCreator(
            image_id=input.initial_revision.image_id,
            resource_spec=ResourceSpec(
                cluster_mode=input.initial_revision.cluster_mode,
                cluster_size=input.initial_revision.cluster_size,
                resource_slots=input.initial_revision.resource_slots,
                resource_opts=input.initial_revision.resource_opts,
            ),
            mounts=mounts_creator,
            execution=ExecutionSpec(
                runtime_variant=input.initial_revision.runtime_variant,
                environ=dict(input.initial_revision.environ)
                if input.initial_revision.environ
                else None,
            ),
        )
        policy: DeploymentPolicyConfig | None = None
        if input.rolling_update is not None:
            policy = DeploymentPolicyConfig(
                strategy=DeploymentStrategy.ROLLING,
                strategy_spec=RollingUpdateSpec(
                    max_surge=input.rolling_update.max_surge,
                    max_unavailable=input.rolling_update.max_unavailable,
                ),
                rollback_on_failure=input.rollback_on_failure,
            )
        elif input.blue_green is not None:
            policy = DeploymentPolicyConfig(
                strategy=DeploymentStrategy.BLUE_GREEN,
                strategy_spec=BlueGreenSpec(
                    auto_promote=input.blue_green.auto_promote,
                    promote_delay_seconds=input.blue_green.promote_delay_seconds,
                ),
                rollback_on_failure=input.rollback_on_failure,
            )
        else:
            policy = DeploymentPolicyConfig(
                strategy=input.strategy,
                strategy_spec=RollingUpdateSpec(),
                rollback_on_failure=input.rollback_on_failure,
            )
        creator = NewDeploymentCreator(
            metadata=DeploymentMetadata(
                name=input.name or f"deployment-{created_user_id.hex[:8]}",
                domain=input.domain_name,
                project=input.project_id,
                resource_group=input.initial_revision.resource_group,
                created_user=created_user_id,
                session_owner=created_user_id,
                created_at=None,
                revision_history_limit=10,
                tag=",".join(input.tags) if input.tags else None,
            ),
            replica_spec=ReplicaSpec(replica_count=input.desired_replica_count),
            network=DeploymentNetworkSpec(
                open_to_public=input.open_to_public,
                preferred_domain_name=input.preferred_domain_name,
            ),
            model_revision=model_revision_creator,
            policy=policy,
        )
        action_result = await self._processors.deployment.create_deployment.wait_for_complete(
            CreateDeploymentAction(creator=creator)
        )
        return CreateDeploymentPayload(deployment=self._deployment_data_to_dto(action_result.data))

    async def admin_search(
        self,
        input: AdminSearchDeploymentsInput,
    ) -> AdminSearchDeploymentsPayload:
        """Search deployments (admin, no scope)."""
        querier = self._build_deployment_querier(input)
        action_result = await self._processors.deployment.search_deployments.wait_for_complete(
            SearchDeploymentsAction(querier=querier)
        )
        return AdminSearchDeploymentsPayload(
            items=[self._deployment_data_to_dto(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def get(self, deployment_id: UUID) -> DeploymentNode:
        """Retrieve a single deployment by ID."""
        action_result = await self._processors.deployment.get_deployment_by_id.wait_for_complete(
            GetDeploymentByIdAction(deployment_id=deployment_id)
        )
        return self._deployment_data_to_dto(action_result.data)

    async def update(
        self,
        input: UpdateDeploymentInput,
        deployment_id: UUID,
    ) -> UpdateDeploymentPayload:
        """Update deployment metadata and configuration."""
        metadata_spec: DeploymentMetadataUpdaterSpec | None = None
        if input.name is not None:
            tag_str: str | None = None
            if not isinstance(input.tags, Sentinel) and input.tags is not None:
                tag_str = ",".join(input.tags)
            elif not isinstance(input.tags, Sentinel) and input.tags is None:
                tag_str = None
            metadata_spec = DeploymentMetadataUpdaterSpec(
                name=OptionalState.update(input.name)
                if input.name is not None
                else OptionalState.nop(),
                tag=(
                    TriState[str].nop()
                    if isinstance(input.tags, Sentinel)
                    else TriState[str].from_graphql(tag_str)
                ),
            )
        elif not isinstance(input.tags, Sentinel):
            tag_str = ",".join(input.tags) if input.tags is not None else None
            metadata_spec = DeploymentMetadataUpdaterSpec(
                tag=TriState[str].from_graphql(tag_str),
            )
        replica_spec: ReplicaSpecUpdaterSpec | None = None
        if input.desired_replicas is not None:
            replica_spec = ReplicaSpecUpdaterSpec(
                desired_replica_count=OptionalState.update(input.desired_replicas),
            )
        spec = DeploymentUpdaterSpec(
            metadata=metadata_spec,
            replica_spec=replica_spec,
        )
        updater: Updater[EndpointRow] = Updater(spec=spec, pk_value=deployment_id)
        action_result = await self._processors.deployment.update_deployment.wait_for_complete(
            UpdateDeploymentAction(updater=updater)
        )
        return UpdateDeploymentPayload(deployment=self._deployment_data_to_dto(action_result.data))

    async def delete(self, input: DeleteDeploymentInput) -> DeleteDeploymentPayload:
        """Delete a deployment."""
        await self._processors.deployment.destroy_deployment.wait_for_complete(
            DestroyDeploymentAction(endpoint_id=input.id)
        )
        return DeleteDeploymentPayload(id=input.id)

    # ------------------------------------------------------------------
    # Access token operations
    # ------------------------------------------------------------------

    async def create_access_token(
        self,
        input: CreateAccessTokenInput,
    ) -> CreateAccessTokenPayload:
        """Create a new access token for a deployment."""
        creator = ModelDeploymentAccessTokenCreator(
            model_deployment_id=input.deployment_id,
            valid_until=input.valid_until,
        )
        action_result = await self._processors.deployment.create_access_token.wait_for_complete(
            CreateAccessTokenAction(creator=creator)
        )
        return CreateAccessTokenPayload(
            access_token=self._access_token_data_to_dto(action_result.data)
        )

    async def search_access_tokens(
        self,
        input: SearchAccessTokensInput,
    ) -> SearchAccessTokensPayload:
        """Search access tokens with filters and pagination."""
        querier = self._build_access_token_querier(input)
        action_result = await self._processors.deployment.search_access_tokens.wait_for_complete(
            SearchAccessTokensAction(querier=querier)
        )
        return SearchAccessTokensPayload(
            items=[self._access_token_data_to_dto(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    # ------------------------------------------------------------------
    # Auto-scaling rule operations
    # ------------------------------------------------------------------

    async def create_rule(
        self,
        input: CreateAutoScalingRuleInput,
    ) -> CreateAutoScalingRulePayload:
        """Create a new auto-scaling rule for a deployment."""
        creator = ModelDeploymentAutoScalingRuleCreator(
            model_deployment_id=input.deployment_id,
            metric_source=input.metric_source,
            metric_name=input.metric_name,
            min_threshold=input.min_threshold,
            max_threshold=input.max_threshold,
            step_size=input.step_size,
            time_window=input.time_window,
            min_replicas=input.min_replicas,
            max_replicas=input.max_replicas,
        )
        action_result = (
            await self._processors.deployment.create_auto_scaling_rule.wait_for_complete(
                CreateAutoScalingRuleAction(creator=creator)
            )
        )
        return CreateAutoScalingRulePayload(
            rule=self._auto_scaling_rule_data_to_dto(action_result.data)
        )

    async def search_rules(
        self,
        input: SearchAutoScalingRulesInput,
    ) -> SearchAutoScalingRulesPayload:
        """Search auto-scaling rules with filters and pagination."""
        querier = self._build_auto_scaling_rule_querier(input)
        action_result = (
            await self._processors.deployment.search_auto_scaling_rules.wait_for_complete(
                SearchAutoScalingRulesAction(querier=querier)
            )
        )
        return SearchAutoScalingRulesPayload(
            items=[self._auto_scaling_rule_data_to_dto(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def get_rule(self, rule_id: UUID) -> GetAutoScalingRulePayload:
        """Retrieve a single auto-scaling rule by ID."""
        action_result = await self._processors.deployment.get_auto_scaling_rule.wait_for_complete(
            GetAutoScalingRuleAction(auto_scaling_rule_id=rule_id)
        )
        return GetAutoScalingRulePayload(
            rule=self._auto_scaling_rule_data_to_dto(action_result.data)
        )

    async def update_rule(
        self,
        input: UpdateAutoScalingRuleInput,
        rule_id: UUID,
    ) -> UpdateAutoScalingRulePayload:
        """Update an auto-scaling rule."""
        modifier = ModelDeploymentAutoScalingRuleModifier(
            metric_source=(
                OptionalState.update(input.metric_source)
                if input.metric_source is not None
                else OptionalState.nop()
            ),
            metric_name=(
                OptionalState.update(input.metric_name)
                if input.metric_name is not None
                else OptionalState.nop()
            ),
            min_threshold=(
                OptionalState.update(input.min_threshold)
                if input.min_threshold is not None
                else OptionalState.nop()
            ),
            max_threshold=(
                OptionalState.update(input.max_threshold)
                if input.max_threshold is not None
                else OptionalState.nop()
            ),
            step_size=(
                OptionalState.update(input.step_size)
                if input.step_size is not None
                else OptionalState.nop()
            ),
            time_window=(
                OptionalState.update(input.time_window)
                if input.time_window is not None
                else OptionalState.nop()
            ),
            min_replicas=(
                OptionalState.update(input.min_replicas)
                if input.min_replicas is not None
                else OptionalState.nop()
            ),
            max_replicas=(
                OptionalState.update(input.max_replicas)
                if input.max_replicas is not None
                else OptionalState.nop()
            ),
        )
        action_result = (
            await self._processors.deployment.update_auto_scaling_rule.wait_for_complete(
                UpdateAutoScalingRuleAction(auto_scaling_rule_id=rule_id, modifier=modifier)
            )
        )
        return UpdateAutoScalingRulePayload(
            rule=self._auto_scaling_rule_data_to_dto(action_result.data)
        )

    async def delete_rule(self, input: DeleteAutoScalingRuleInput) -> DeleteAutoScalingRulePayload:
        """Delete an auto-scaling rule."""
        await self._processors.deployment.delete_auto_scaling_rule.wait_for_complete(
            DeleteAutoScalingRuleAction(auto_scaling_rule_id=input.id)
        )
        return DeleteAutoScalingRulePayload(id=input.id)

    # ------------------------------------------------------------------
    # Deployment policy operations
    # ------------------------------------------------------------------

    async def get_policy(self, deployment_id: UUID) -> GetDeploymentPolicyPayload:
        """Retrieve a deployment policy by deployment ID."""
        action_result = await self._processors.deployment.get_deployment_policy.wait_for_complete(
            GetDeploymentPolicyAction(endpoint_id=deployment_id)
        )
        return GetDeploymentPolicyPayload(policy=self._policy_data_to_dto(action_result.data))

    async def search_policies(
        self,
        input: SearchDeploymentPoliciesInput,
    ) -> SearchDeploymentPoliciesPayload:
        """Search deployment policies with filters and pagination."""
        querier = self._build_policy_querier(input)
        action_result = (
            await self._processors.deployment.search_deployment_policies.wait_for_complete(
                SearchDeploymentPoliciesAction(querier=querier)
            )
        )
        return SearchDeploymentPoliciesPayload(
            items=[self._policy_data_to_dto(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def upsert_policy(
        self,
        input: UpsertDeploymentPolicyInput,
    ) -> UpsertDeploymentPolicyPayload:
        """Create or update a deployment policy."""
        strategy_spec: RollingUpdateSpec | BlueGreenSpec
        match input.strategy:
            case DeploymentStrategy.ROLLING:
                rolling = input.rolling_update
                strategy_spec = RollingUpdateSpec(
                    max_surge=rolling.max_surge if rolling is not None else 1,
                    max_unavailable=rolling.max_unavailable if rolling is not None else 0,
                )
            case DeploymentStrategy.BLUE_GREEN:
                bg = input.blue_green
                strategy_spec = BlueGreenSpec(
                    auto_promote=bg.auto_promote if bg is not None else False,
                    promote_delay_seconds=bg.promote_delay_seconds if bg is not None else 0,
                )
        upserter = DeploymentPolicyUpserter(
            deployment_id=input.deployment_id,
            strategy=input.strategy,
            strategy_spec=strategy_spec,
            rollback_on_failure=input.rollback_on_failure,
        )
        action_result = (
            await self._processors.deployment.upsert_deployment_policy.wait_for_complete(
                UpsertDeploymentPolicyAction(upserter=upserter)
            )
        )
        return UpsertDeploymentPolicyPayload(policy=self._policy_data_to_dto(action_result.data))

    # ------------------------------------------------------------------
    # Model revision operations
    # ------------------------------------------------------------------

    async def add_revision(
        self,
        input: AddRevisionInput,
    ) -> AddRevisionPayload:
        """Add a new model revision to a deployment."""
        mounts_creator = VFolderMountsCreator(
            model_vfolder_id=input.revision.model_vfolder_id,
            model_definition_path=input.revision.model_definition_path,
            model_mount_destination=input.revision.model_mount_destination,
            extra_mounts=[
                MountInfo(
                    vfolder_id=m.vfolder_id,
                    kernel_path=None,
                )
                for m in (input.revision.extra_mounts or [])
            ],
        )
        adder = ModelRevisionCreator(
            image_id=input.revision.image_id,
            resource_spec=ResourceSpec(
                cluster_mode=input.revision.cluster_mode,
                cluster_size=input.revision.cluster_size,
                resource_slots=input.revision.resource_slots,
                resource_opts=input.revision.resource_opts,
            ),
            mounts=mounts_creator,
            execution=ExecutionSpec(
                runtime_variant=input.revision.runtime_variant,
                environ=dict(input.revision.environ) if input.revision.environ else None,
            ),
        )
        action_result = await self._processors.deployment.add_model_revision.wait_for_complete(
            AddModelRevisionAction(model_deployment_id=input.deployment_id, adder=adder)
        )
        return AddRevisionPayload(revision=self._revision_data_to_dto(action_result.revision))

    async def get_revision(self, revision_id: UUID) -> RevisionNode:
        """Retrieve a single revision by ID."""
        action_result = await self._processors.deployment.get_revision_by_id.wait_for_complete(
            GetRevisionByIdAction(revision_id=revision_id)
        )
        return self._revision_data_to_dto(action_result.data)

    async def search_revisions(
        self,
        input: AdminSearchRevisionsInput,
    ) -> AdminSearchRevisionsPayload:
        """Search model revisions with filters and pagination."""
        querier = self._build_revision_querier(input)
        action_result = await self._processors.deployment.search_revisions.wait_for_complete(
            SearchRevisionsAction(querier=querier)
        )
        return AdminSearchRevisionsPayload(
            items=[self._revision_data_to_dto(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    # ------------------------------------------------------------------
    # Route operations
    # ------------------------------------------------------------------

    async def search_routes(
        self,
        input: SearchRoutesInput,
    ) -> SearchRoutesPayload:
        """Search routes with filters and pagination."""
        querier = self._build_route_querier(input)
        action_result = await self._processors.deployment.search_routes.wait_for_complete(
            SearchRoutesAction(querier=querier)
        )
        return SearchRoutesPayload(
            items=[self._route_info_to_dto(item) for item in action_result.routes],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def update_route_traffic(
        self,
        route_id: UUID,
        traffic_status: RouteTrafficStatus,
    ) -> RouteNode:
        """Update the traffic status of a route."""
        action_result = (
            await self._processors.deployment.update_route_traffic_status.wait_for_complete(
                UpdateRouteTrafficStatusAction(
                    route_id=route_id,
                    traffic_status=ManagerRouteTrafficStatus(traffic_status.value),
                )
            )
        )
        return self._route_info_to_dto(action_result.route)

    # ------------------------------------------------------------------
    # Querier builders
    # ------------------------------------------------------------------

    def _build_deployment_querier(self, input: AdminSearchDeploymentsInput) -> BatchQuerier:
        conditions: list[QueryCondition] = []
        if input.filter:
            f = input.filter
            if f.name is not None:
                condition = self.convert_string_filter(
                    f.name,
                    contains_factory=DeploymentConditions.by_name_contains,
                    equals_factory=DeploymentConditions.by_name_equals,
                    starts_with_factory=DeploymentConditions.by_name_starts_with,
                    ends_with_factory=DeploymentConditions.by_name_ends_with,
                )
                if condition is not None:
                    conditions.append(condition)
            if f.open_to_public is not None:
                conditions.append(DeploymentConditions.by_open_to_public(f.open_to_public))
        orders: list[QueryOrder] = (
            self._convert_deployment_orders(input.order) if input.order else []
        )
        orders.append(DeploymentOrders.created_at(ascending=False))
        orders.append(DeploymentOrders.name(ascending=True))
        pagination = OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )
        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _build_revision_querier(self, input: AdminSearchRevisionsInput) -> BatchQuerier:
        conditions: list[QueryCondition] = []
        if input.filter:
            f = input.filter
            if f.deployment_id is not None:
                conditions.append(RevisionConditions.by_deployment_id(f.deployment_id))
            if f.name is not None:
                condition = self.convert_string_filter(
                    f.name,
                    contains_factory=RevisionConditions.by_name_contains,
                    equals_factory=RevisionConditions.by_name_equals,
                    starts_with_factory=RevisionConditions.by_name_starts_with,
                    ends_with_factory=RevisionConditions.by_name_ends_with,
                )
                if condition is not None:
                    conditions.append(condition)
        orders: list[QueryOrder] = self._convert_revision_orders(input.order) if input.order else []
        orders.append(RevisionOrders.created_at(ascending=False))
        pagination = OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )
        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _build_route_querier(self, input: SearchRoutesInput) -> BatchQuerier:
        conditions: list[QueryCondition] = []
        if input.filter:
            f = input.filter
            if f.deployment_id is not None:
                conditions.append(RouteConditions.by_endpoint_id(f.deployment_id))
            if f.status is not None:
                if f.status.equals is not None:
                    conditions.append(
                        RouteConditions.by_statuses([ManagerRouteStatus(f.status.equals.value)])
                    )
                elif f.status.in_ is not None:
                    conditions.append(
                        RouteConditions.by_statuses([
                            ManagerRouteStatus(s.value) for s in f.status.in_
                        ])
                    )
            if f.traffic_status is not None:
                if f.traffic_status.equals is not None:
                    conditions.append(
                        RouteConditions.by_traffic_statuses([
                            ManagerRouteTrafficStatus(f.traffic_status.equals.value)
                        ])
                    )
                elif f.traffic_status.in_ is not None:
                    conditions.append(
                        RouteConditions.by_traffic_statuses([
                            ManagerRouteTrafficStatus(s.value) for s in f.traffic_status.in_
                        ])
                    )
        orders: list[QueryOrder] = self._convert_route_orders(input.order) if input.order else []
        orders.append(RouteOrders.created_at(ascending=False))
        pagination = OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )
        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _build_access_token_querier(self, input: SearchAccessTokensInput) -> BatchQuerier:
        conditions: list[QueryCondition] = []
        if input.filter and input.filter.deployment_id is not None:
            conditions.append(AccessTokenConditions.by_endpoint_id(input.filter.deployment_id))
        orders: list[QueryOrder] = (
            [
                AccessTokenOrders.created_at(ascending=o.direction == OrderDirection.ASC)
                for o in input.order
            ]
            if input.order
            else []
        )
        orders.append(AccessTokenOrders.created_at(ascending=False))
        pagination = OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )
        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _build_auto_scaling_rule_querier(self, input: SearchAutoScalingRulesInput) -> BatchQuerier:
        conditions: list[QueryCondition] = []
        if input.filter and input.filter.deployment_id is not None:
            conditions.append(
                AutoScalingRuleConditions.by_deployment_id(input.filter.deployment_id)
            )
        orders: list[QueryOrder] = (
            [
                AutoScalingRuleOrders.created_at(ascending=o.direction == OrderDirection.ASC)
                for o in input.order
            ]
            if input.order
            else []
        )
        orders.append(AutoScalingRuleOrders.created_at(ascending=False))
        pagination = OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )
        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _build_policy_querier(self, input: SearchDeploymentPoliciesInput) -> BatchQuerier:
        conditions: list[QueryCondition] = []
        if input.filter and input.filter.deployment_id is not None:
            conditions.append(
                DeploymentPolicyConditions.by_endpoint_ids([input.filter.deployment_id])
            )
        pagination = OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )
        return BatchQuerier(conditions=conditions, orders=[], pagination=pagination)

    # ------------------------------------------------------------------
    # Order converters
    # ------------------------------------------------------------------

    @staticmethod
    def _convert_deployment_orders(orders: list[DeploymentOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for o in orders:
            ascending = o.direction == OrderDirection.ASC
            match o.field:
                case DeploymentOrderField.NAME:
                    result.append(DeploymentOrders.name(ascending))
                case DeploymentOrderField.CREATED_AT:
                    result.append(DeploymentOrders.created_at(ascending))
                case DeploymentOrderField.UPDATED_AT:
                    result.append(DeploymentOrders.updated_at(ascending))
        return result

    @staticmethod
    def _convert_revision_orders(orders: list[RevisionOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for o in orders:
            ascending = o.direction == OrderDirection.ASC
            match o.field:
                case RevisionOrderField.NAME:
                    result.append(RevisionOrders.name(ascending))
                case RevisionOrderField.CREATED_AT:
                    result.append(RevisionOrders.created_at(ascending))
        return result

    @staticmethod
    def _convert_route_orders(orders: list[RouteOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for o in orders:
            ascending = o.direction == OrderDirection.ASC
            match o.field:
                case RouteOrderField.CREATED_AT:
                    result.append(RouteOrders.created_at(ascending))
                case RouteOrderField.STATUS:
                    result.append(RouteOrders.status(ascending))
                case RouteOrderField.TRAFFIC_RATIO:
                    result.append(RouteOrders.traffic_ratio(ascending))
        return result

    # ------------------------------------------------------------------
    # Data → DTO converters
    # ------------------------------------------------------------------

    @staticmethod
    def _deployment_data_to_dto(data: ModelDeploymentData) -> DeploymentNode:
        policy_info: DeploymentPolicyInfo | None = None
        if data.policy is not None:
            policy_spec = data.policy.strategy_spec
            rolling: RollingUpdateConfigInfo | None = None
            blue_green: BlueGreenConfigInfo | None = None
            if isinstance(policy_spec, RollingUpdateSpec):
                rolling = RollingUpdateConfigInfo(
                    max_surge=policy_spec.max_surge,
                    max_unavailable=policy_spec.max_unavailable,
                )
            elif isinstance(policy_spec, BlueGreenSpec):
                blue_green = BlueGreenConfigInfo(
                    auto_promote=policy_spec.auto_promote,
                    promote_delay_seconds=policy_spec.promote_delay_seconds,
                )
            policy_info = DeploymentPolicyInfo(
                strategy=data.policy.strategy,
                rollback_on_failure=data.policy.rollback_on_failure,
                rolling_update=rolling,
                blue_green=blue_green,
            )
        return DeploymentNode(
            id=data.id,
            basic=DeploymentBasicInfo(
                name=data.metadata.name,
                status=data.metadata.status,
                tags=data.metadata.tags,
                project_id=data.metadata.project_id,
                domain_name=data.metadata.domain_name,
                created_user_id=data.created_user_id,
            ),
            network=NetworkConfigInfo(
                open_to_public=data.network_access.open_to_public,
                url=data.network_access.url,
                preferred_domain_name=data.network_access.preferred_domain_name,
            ),
            replica_state=ReplicaStateInfo(
                desired_replica_count=data.replica_state.desired_replica_count,
                replica_ids=data.replica_state.replica_ids,
            ),
            default_deployment_strategy=data.default_deployment_strategy,
            current_revision=(
                DeploymentAdapter._revision_data_to_dto(data.revision)
                if data.revision is not None
                else None
            ),
            policy=policy_info,
            created_at=data.metadata.created_at,
            updated_at=data.metadata.updated_at,
        )

    @staticmethod
    def _revision_data_to_dto(data: ModelRevisionData) -> RevisionNode:
        return RevisionNode(
            id=data.id,
            name=data.name,
            revision_info=DeploymentRevisionInfo(
                cluster_mode=data.cluster_config.mode,
                cluster_size=data.cluster_config.size,
                resource_group=data.resource_config.resource_group_name,
                resource_slots=dict(data.resource_config.resource_slot),
                image_id=data.image_id,
                runtime_variant=data.model_runtime_config.runtime_variant,
                model_vfolder_id=data.model_mount_config.vfolder_id,
                model_mount_destination=data.model_mount_config.mount_destination,
                model_definition_path=data.model_mount_config.definition_path,
            ),
            created_at=data.created_at,
            extra_mounts=[
                ExtraVFolderMountNode(
                    vfolder_id=m.vfolder_id,
                    mount_destination=m.mount_destination,
                )
                for m in data.extra_vfolder_mounts
            ],
        )

    @staticmethod
    def _route_info_to_dto(data: RouteInfo) -> RouteNode:
        return RouteNode(
            id=data.route_id,
            endpoint_id=data.endpoint_id,
            session_id=str(data.session_id) if data.session_id is not None else None,
            status=RouteStatus(data.status.value),
            traffic_ratio=data.traffic_ratio,
            created_at=data.created_at,
            revision_id=data.revision_id,
            traffic_status=RouteTrafficStatus(data.traffic_status.value),
            error_data=data.error_data,
        )

    @staticmethod
    def _access_token_data_to_dto(data: ModelDeploymentAccessTokenData) -> AccessTokenNode:
        return AccessTokenNode(
            id=data.id,
            token=data.token,
            valid_until=data.valid_until,
            created_at=data.created_at,
        )

    @staticmethod
    def _auto_scaling_rule_data_to_dto(
        data: ModelDeploymentAutoScalingRuleData,
    ) -> AutoScalingRuleNode:
        return AutoScalingRuleNode(
            id=data.id,
            deployment_id=data.model_deployment_id,
            metric_source=data.metric_source,
            metric_name=data.metric_name,
            min_threshold=data.min_threshold,
            max_threshold=data.max_threshold,
            step_size=data.step_size,
            time_window=data.time_window,
            min_replicas=data.min_replicas,
            max_replicas=data.max_replicas,
            created_at=data.created_at,
            last_triggered_at=data.last_triggered_at,
        )

    @staticmethod
    def _policy_data_to_dto(data: DeploymentPolicyData) -> DeploymentPolicyNode:
        rolling: RollingUpdateConfigInfo | None = None
        blue_green: BlueGreenConfigInfo | None = None
        if isinstance(data.strategy_spec, RollingUpdateSpec):
            rolling = RollingUpdateConfigInfo(
                max_surge=data.strategy_spec.max_surge,
                max_unavailable=data.strategy_spec.max_unavailable,
            )
        elif isinstance(data.strategy_spec, BlueGreenSpec):
            blue_green = BlueGreenConfigInfo(
                auto_promote=data.strategy_spec.auto_promote,
                promote_delay_seconds=data.strategy_spec.promote_delay_seconds,
            )
        return DeploymentPolicyNode(
            id=data.id,
            deployment_id=data.endpoint,
            strategy=data.strategy,
            rollback_on_failure=data.rollback_on_failure,
            rolling_update=rolling,
            blue_green=blue_green,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )
