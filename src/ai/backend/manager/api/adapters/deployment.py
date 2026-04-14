"""Deployment adapter bridging DTOs and Processors."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from functools import lru_cache
from pathlib import PurePosixPath
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.api_handlers import Sentinel
from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.model_deployment.types import (
    DeploymentStrategy,
    RouteHealthStatus,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.common.dto.manager.v2.auto_scaling_rule.request import (
    BulkDeleteAutoScalingRulesInput,
    CreateAutoScalingRuleInput,
    DeleteAutoScalingRuleInput,
    UpdateAutoScalingRuleInput,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    ActivateRevisionInput,
    AddRevisionGQLInputDTO,
    AdminSearchDeploymentsInput,
    AdminSearchRevisionsInput,
    BulkDeleteAccessTokensInput,
    CreateAccessTokenInput,
    CreateDeploymentInput,
    DeleteAccessTokenInput,
    DeleteDeploymentInput,
    DeploymentOrder,
    ReplicaOrder,
    RevisionOrder,
    RouteOrder,
    SearchAccessTokensInput,
    SearchAutoScalingRulesInput,
    SearchDeploymentPoliciesInput,
    SearchReplicasInput,
    SearchRoutesInput,
    SyncReplicaInput,
    UpdateDeploymentInput,
    UpsertDeploymentPolicyInput,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    AccessTokenNode,
    ActivateRevisionPayload,
    AddRevisionPayload,
    AdminSearchDeploymentsPayload,
    AdminSearchRevisionsPayload,
    AutoScalingRuleNode,
    BulkDeleteAccessTokensPayload,
    BulkDeleteAutoScalingRulesPayload,
    CreateAccessTokenPayload,
    CreateAutoScalingRulePayload,
    CreateDeploymentPayload,
    DeleteAccessTokenPayload,
    DeleteAutoScalingRulePayload,
    DeleteDeploymentPayload,
    DeploymentNode,
    DeploymentPolicyNode,
    GetAccessTokenPayload,
    GetAutoScalingRulePayload,
    GetDeploymentPolicyPayload,
    ReplicaNode,
    RevisionNode,
    RouteNode,
    SearchAccessTokensPayload,
    SearchAutoScalingRulesPayload,
    SearchDeploymentPoliciesPayload,
    SearchReplicasPayload,
    SearchRoutesPayload,
    SyncReplicaPayload,
    UpdateAutoScalingRulePayload,
    UpdateDeploymentPayload,
    UpsertDeploymentPolicyPayload,
)
from ai.backend.common.dto.manager.v2.deployment.types import (
    BlueGreenConfigInfo,
    BlueGreenStrategySpecInfo,
    ClusterConfigInfoDTO,
    DeploymentMetadataInfoDTO,
    DeploymentNetworkAccessInfoDTO,
    DeploymentOrderField,
    DeploymentPolicyInfo,
    DeploymentStrategyInfoDTO,
    EnvironmentVariableEntryInfoDTO,
    EnvironmentVariablesInfoDTO,
    ExtraVFolderMountGQLDTO,
    ModelDefinitionInfoDTO,
    ModelMountConfigInfoDTO,
    ModelRuntimeConfigInfoDTO,
    OrderDirection,
    ReplicaOrderField,
    ReplicaStateInfo,
    ResourceConfigInfoDTO,
    RevisionOrderField,
    RollingUpdateConfigInfo,
    RollingUpdateStrategySpecInfo,
    RouteOrderField,
)
from ai.backend.common.dto.manager.v2.resource_slot.request import (
    AllocatedResourceSlotFilter,
    SearchAllocatedResourceSlotsInput,
)
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    AllocatedResourceSlotNode,
    SearchAllocatedResourceSlotsPayload,
)
from ai.backend.common.dto.manager.v2.resource_slot.types import (
    ResourceOptsEntryInfoDTO,
    ResourceOptsInfoDTO,
)
from ai.backend.common.types import RuntimeVariant
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
    AccessTokenSearchScope,
    AutoScalingRuleSearchScope,
    DeploymentMetadata,
    DeploymentNetworkSpec,
    DeploymentPolicyData,
    ExecutionSpec,
    ModelDeploymentAccessTokenData,
    ModelDeploymentAutoScalingRuleData,
    ModelDeploymentData,
    ModelReplicaData,
    ModelRevisionData,
    MountInfo,
    ReplicaSearchScope,
    ReplicaSpec,
    ResourceSpec,
    RevisionSearchScope,
    RouteInfo,
    RouteSearchScope,
)
from ai.backend.manager.data.deployment.types import (
    RouteHealthStatus as ManagerRouteHealthStatus,
)
from ai.backend.manager.data.deployment.types import (
    RouteStatus as ManagerRouteStatus,
)
from ai.backend.manager.data.deployment.types import (
    RouteTrafficStatus as ManagerRouteTrafficStatus,
)
from ai.backend.manager.data.deployment.upserter import DeploymentPolicyUpserter
from ai.backend.manager.errors.deployment import DeploymentRevisionNotFound
from ai.backend.manager.errors.service import EndpointTokenNotFound
from ai.backend.manager.models.deployment_policy import BlueGreenSpec, RollingUpdateSpec
from ai.backend.manager.models.deployment_policy.conditions import DeploymentPolicyConditions
from ai.backend.manager.models.deployment_policy.row import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision.conditions import RevisionConditions
from ai.backend.manager.models.deployment_revision.orders import RevisionOrders
from ai.backend.manager.models.endpoint import (
    EndpointAutoScalingRuleRow,
    EndpointRow,
    EndpointTokenRow,
)
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
from ai.backend.manager.models.resource_slot.conditions import RevisionResourceSlotConditions
from ai.backend.manager.models.resource_slot.orders import (
    ALLOCATED_SLOT_DEFAULT_BACKWARD_ORDER,
    ALLOCATED_SLOT_DEFAULT_FORWARD_ORDER,
    ALLOCATED_SLOT_REVISION_TIEBREAKER,
    resolve_allocated_slot_revision_order,
)
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.routing.conditions import RouteConditions
from ai.backend.manager.models.routing.orders import RouteOrders
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    NoPagination,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
    Updater,
    combine_conditions_or,
)
from ai.backend.manager.repositories.deployment.updaters import (
    DeploymentMetadataUpdaterSpec,
    DeploymentNetworkSpecUpdaterSpec,
    DeploymentUpdaterSpec,
    ReplicaSpecUpdaterSpec,
    RevisionStateUpdaterSpec,
)
from ai.backend.manager.services.deployment.actions.access_token.bulk_delete_access_tokens import (
    BulkDeleteAccessTokensAction,
)
from ai.backend.manager.services.deployment.actions.access_token.create_access_token import (
    CreateAccessTokenAction,
)
from ai.backend.manager.services.deployment.actions.access_token.delete_access_token import (
    DeleteAccessTokenAction,
)
from ai.backend.manager.services.deployment.actions.access_token.get_access_token import (
    GetAccessTokenAction,
)
from ai.backend.manager.services.deployment.actions.access_token.search_access_tokens import (
    SearchAccessTokensAction,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.bulk_delete_auto_scaling_rules import (
    BulkDeleteAutoScalingRulesAction,
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
from ai.backend.manager.services.deployment.actions.get_replica_by_id import (
    GetReplicaByIdAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.add_model_revision import (
    AddModelRevisionAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.get_revision_by_id import (
    GetRevisionByIdAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.search_revision_resource_slots import (
    SearchRevisionResourceSlotsAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.search_revisions import (
    SearchRevisionsAction,
)
from ai.backend.manager.services.deployment.actions.revision_operations import (
    ActivateRevisionAction,
)
from ai.backend.manager.services.deployment.actions.route.search_routes import SearchRoutesAction
from ai.backend.manager.services.deployment.actions.route.update_route_traffic_status import (
    UpdateRouteTrafficStatusAction,
)
from ai.backend.manager.services.deployment.actions.search_deployments import (
    SearchDeploymentsAction,
)
from ai.backend.manager.services.deployment.actions.search_replicas import SearchReplicasAction
from ai.backend.manager.services.deployment.actions.sync_replicas import SyncReplicaAction
from ai.backend.manager.services.deployment.actions.update_deployment import UpdateDeploymentAction
from ai.backend.manager.types import OptionalState, TriState

from .base import BaseAdapter
from .pagination import PaginationSpec

DEFAULT_PAGINATION_LIMIT = 10


@lru_cache(maxsize=1)
def _get_deployment_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=DeploymentOrders.created_at(ascending=False),
        backward_order=DeploymentOrders.created_at(ascending=True),
        forward_condition_factory=DeploymentConditions.by_cursor_forward,
        backward_condition_factory=DeploymentConditions.by_cursor_backward,
        tiebreaker_order=EndpointRow.id.asc(),
    )


def _get_deployment_policy_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=DeploymentPolicyRow.created_at.desc(),
        backward_order=DeploymentPolicyRow.created_at.asc(),
        forward_condition_factory=DeploymentConditions.by_cursor_forward,
        backward_condition_factory=DeploymentConditions.by_cursor_backward,
        tiebreaker_order=DeploymentPolicyRow.id.asc(),
    )


@lru_cache(maxsize=1)
def _get_revision_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=RevisionOrders.created_at(ascending=False),
        backward_order=RevisionOrders.created_at(ascending=True),
        forward_condition_factory=RevisionConditions.by_cursor_forward,
        backward_condition_factory=RevisionConditions.by_cursor_backward,
        tiebreaker_order=DeploymentRevisionRow.id.asc(),
    )


@lru_cache(maxsize=1)
def _get_route_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=RouteOrders.created_at(ascending=False),
        backward_order=RouteOrders.created_at(ascending=True),
        forward_condition_factory=RouteConditions.by_cursor_forward,
        backward_condition_factory=RouteConditions.by_cursor_backward,
        tiebreaker_order=RoutingRow.id.asc(),
    )


@lru_cache(maxsize=1)
def _get_access_token_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=AccessTokenOrders.created_at(ascending=False),
        backward_order=AccessTokenOrders.created_at(ascending=True),
        forward_condition_factory=AccessTokenConditions.by_cursor_forward,
        backward_condition_factory=AccessTokenConditions.by_cursor_backward,
        tiebreaker_order=EndpointTokenRow.id.asc(),
    )


@lru_cache(maxsize=1)
def _get_auto_scaling_rule_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=AutoScalingRuleOrders.created_at(ascending=False),
        backward_order=AutoScalingRuleOrders.created_at(ascending=True),
        forward_condition_factory=AutoScalingRuleConditions.by_cursor_forward,
        backward_condition_factory=AutoScalingRuleConditions.by_cursor_backward,
        tiebreaker_order=EndpointAutoScalingRuleRow.id.asc(),
    )


@lru_cache(maxsize=1)
def _get_replica_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=RouteOrders.created_at(ascending=False),
        backward_order=RouteOrders.created_at(ascending=True),
        forward_condition_factory=RouteConditions.by_cursor_forward,
        backward_condition_factory=RouteConditions.by_cursor_backward,
        tiebreaker_order=RoutingRow.id.asc(),
    )


@lru_cache(maxsize=1)
def _get_revision_resource_slot_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=ALLOCATED_SLOT_DEFAULT_FORWARD_ORDER,
        backward_order=ALLOCATED_SLOT_DEFAULT_BACKWARD_ORDER,
        forward_condition_factory=RevisionResourceSlotConditions.by_cursor_forward,
        backward_condition_factory=RevisionResourceSlotConditions.by_cursor_backward,
        tiebreaker_order=ALLOCATED_SLOT_REVISION_TIEBREAKER,
    )


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
        initial_revision = input.initial_revision
        model_revision_creator: ModelRevisionCreator | None = None
        resource_group_name: str | None = None
        if initial_revision is not None:
            mounts_creator = VFolderMountsCreator(
                model_vfolder_id=initial_revision.model_mount_config.vfolder_id,
                model_definition_path=initial_revision.model_mount_config.definition_path,
                model_mount_destination=initial_revision.model_mount_config.mount_destination,
                extra_mounts=[
                    MountInfo(
                        vfolder_id=m.vfolder_id,
                        kernel_path=PurePosixPath(m.mount_destination)
                        if m.mount_destination
                        else None,
                    )
                    for m in (initial_revision.extra_mounts or [])
                ],
            )
            model_revision_creator = ModelRevisionCreator(
                image_id=initial_revision.image.id,
                resource_spec=ResourceSpec(
                    cluster_mode=initial_revision.cluster_config.mode,
                    cluster_size=initial_revision.cluster_config.size,
                    resource_slots={
                        e.resource_type: e.quantity
                        for e in initial_revision.resource_config.resource_slots.entries
                    },
                    resource_opts={
                        e.name: e.value
                        for e in initial_revision.resource_config.resource_opts.entries
                    }
                    if initial_revision.resource_config.resource_opts
                    else None,
                ),
                mounts=mounts_creator,
                model_definition=initial_revision.model_definition,
                revision_preset_id=initial_revision.revision_preset_id,
                execution=ExecutionSpec(
                    runtime_variant=RuntimeVariant(
                        initial_revision.model_runtime_config.runtime_variant
                    ),
                    environ={
                        e.name: e.value
                        for e in initial_revision.model_runtime_config.environ.entries
                    }
                    if initial_revision.model_runtime_config.environ
                    else None,
                ),
            )
            resource_group_name = initial_revision.resource_config.resource_group.name
        strategy = input.default_deployment_strategy
        policy: DeploymentPolicyConfig | None = None
        if strategy.rolling_update is not None:
            policy = DeploymentPolicyConfig(
                strategy=DeploymentStrategy.ROLLING,
                strategy_spec=RollingUpdateSpec(
                    max_surge=strategy.rolling_update.max_surge,
                    max_unavailable=strategy.rolling_update.max_unavailable,
                ),
            )
        elif strategy.blue_green is not None:
            policy = DeploymentPolicyConfig(
                strategy=DeploymentStrategy.BLUE_GREEN,
                strategy_spec=BlueGreenSpec(
                    auto_promote=strategy.blue_green.auto_promote,
                    promote_delay_seconds=strategy.blue_green.promote_delay_seconds,
                ),
            )
        else:
            policy = DeploymentPolicyConfig(
                strategy=strategy.type,
                strategy_spec=RollingUpdateSpec(),
            )
        meta = input.metadata
        creator = NewDeploymentCreator(
            metadata=DeploymentMetadata(
                name=meta.name or f"deployment-{created_user_id.hex[:8]}",
                domain=meta.domain_name,
                project=meta.project_id,
                resource_group=resource_group_name or "default",
                created_user=created_user_id,
                session_owner=created_user_id,
                created_at=None,
                revision_history_limit=10,
                tag=",".join(meta.tags) if meta.tags else None,
            ),
            replica_spec=ReplicaSpec(replica_count=input.desired_replica_count),
            network=DeploymentNetworkSpec(
                open_to_public=input.network_access.open_to_public,
                preferred_domain_name=input.network_access.preferred_domain_name,
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

    async def my_search(
        self,
        input: AdminSearchDeploymentsInput,
    ) -> AdminSearchDeploymentsPayload:
        """Search deployments owned by the current user."""
        user = current_user()
        if user is None:
            raise RuntimeError("No authenticated user in context")
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
                    in_factory=DeploymentConditions.by_name_in,
                )
                if condition is not None:
                    conditions.append(condition)
            if f.open_to_public is not None:
                conditions.append(DeploymentConditions.by_open_to_public(f.open_to_public))
        orders: list[QueryOrder] = (
            self._convert_deployment_orders(input.order) if input.order else []
        )

        def _by_created_user() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointRow.created_user == user.user_id

        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_get_deployment_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
            base_conditions=[_by_created_user],
        )
        action_result = await self._processors.deployment.search_deployments.wait_for_complete(
            SearchDeploymentsAction(querier=querier)
        )
        return AdminSearchDeploymentsPayload(
            items=[self._deployment_data_to_dto(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def project_search(
        self,
        project_id: UUID,
        input: AdminSearchDeploymentsInput,
    ) -> AdminSearchDeploymentsPayload:
        """Search deployments within a specific project."""
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
                    in_factory=DeploymentConditions.by_name_in,
                )
                if condition is not None:
                    conditions.append(condition)
            if f.open_to_public is not None:
                conditions.append(DeploymentConditions.by_open_to_public(f.open_to_public))
        orders: list[QueryOrder] = (
            self._convert_deployment_orders(input.order) if input.order else []
        )

        def _by_project_id() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointRow.project == project_id

        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_get_deployment_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
            base_conditions=[_by_project_id],
        )
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

    async def get_current_revision(self, deployment_id: UUID) -> RevisionNode:
        """Retrieve the current active revision of a deployment."""
        deployment = await self.get(deployment_id)
        if deployment.current_revision_id is None:
            raise DeploymentRevisionNotFound(f"Deployment {deployment_id} has no current revision")
        return await self.get_revision(deployment.current_revision_id)

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
        if input.desired_replica_count is not None:
            replica_spec = ReplicaSpecUpdaterSpec(
                desired_replica_count=OptionalState.update(input.desired_replica_count),
            )
        network_spec: DeploymentNetworkSpecUpdaterSpec | None = None
        if input.open_to_public is not None:
            network_spec = DeploymentNetworkSpecUpdaterSpec(
                open_to_public=OptionalState.from_graphql(input.open_to_public),
            )
        revision_state_spec: RevisionStateUpdaterSpec | None = None
        if input.active_revision_id is not None:
            revision_state_spec = RevisionStateUpdaterSpec(
                current_revision=TriState[UUID].from_graphql(input.active_revision_id),
            )
        spec = DeploymentUpdaterSpec(
            metadata=metadata_spec,
            replica_spec=replica_spec,
            network=network_spec,
            revision_state=revision_state_spec,
        )
        updater: Updater[EndpointRow] = Updater(spec=spec, pk_value=deployment_id)
        action_result = await self._processors.deployment.update_deployment.wait_for_complete(
            UpdateDeploymentAction(updater=updater)
        )
        return UpdateDeploymentPayload(deployment=self._deployment_data_to_dto(action_result.data))

    async def sync_replicas(self, input: SyncReplicaInput) -> SyncReplicaPayload:
        """Force sync replica information for a deployment."""
        await self._processors.deployment.sync_replicas.wait_for_complete(
            SyncReplicaAction(deployment_id=input.model_deployment_id)
        )
        return SyncReplicaPayload(success=True)

    async def activate_revision(self, input: ActivateRevisionInput) -> ActivateRevisionPayload:
        """Activate a specific revision as the current revision."""
        action_result = await self._processors.deployment.activate_revision.wait_for_complete(
            ActivateRevisionAction(
                deployment_id=input.deployment_id,
                revision_id=input.revision_id,
            )
        )
        return ActivateRevisionPayload(
            deployment=self._deployment_data_to_dto(action_result.deployment),
            previous_revision_id=action_result.previous_revision_id,
            activated_revision_id=action_result.activated_revision_id,
            deployment_policy=self._policy_data_to_dto(action_result.deployment_policy),
        )

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
            expires_at=input.expires_at,
        )
        action_result = await self._processors.deployment.create_access_token.wait_for_complete(
            CreateAccessTokenAction(creator=creator)
        )
        return CreateAccessTokenPayload(
            access_token=self._access_token_data_to_dto(action_result.data)
        )

    async def get_access_token(
        self,
        token_id: UUID,
    ) -> GetAccessTokenPayload:
        """Get a single access token by ID."""
        action_result = await self._processors.deployment.get_access_token.wait_for_complete(
            GetAccessTokenAction(access_token_id=token_id)
        )
        return GetAccessTokenPayload(
            access_token=self._access_token_data_to_dto(action_result.data)
        )

    async def delete_access_token(
        self,
        input: DeleteAccessTokenInput,
    ) -> DeleteAccessTokenPayload:
        """Delete an access token."""
        action_result = await self._processors.deployment.delete_access_token.wait_for_complete(
            DeleteAccessTokenAction(access_token_id=input.id)
        )
        if not action_result.success:
            raise EndpointTokenNotFound(f"Access token {input.id} not found")
        return DeleteAccessTokenPayload(id=input.id)

    async def bulk_delete_access_tokens(
        self,
        input: BulkDeleteAccessTokensInput,
    ) -> BulkDeleteAccessTokensPayload:
        """Bulk delete access tokens."""
        action_result = (
            await self._processors.deployment.bulk_delete_access_tokens.wait_for_complete(
                BulkDeleteAccessTokensAction(access_token_ids=input.ids)
            )
        )
        return BulkDeleteAccessTokensPayload(ids=action_result.deleted_ids)

    async def search_access_tokens(
        self,
        scope: AccessTokenSearchScope,
        input: SearchAccessTokensInput,
    ) -> SearchAccessTokensPayload:
        """Search access tokens scoped to a specific deployment."""
        querier = self._build_access_token_querier(input, scope=scope)
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
            model_deployment_id=input.model_deployment_id,
            metric_source=input.metric_source,
            metric_name=input.metric_name,
            min_threshold=input.min_threshold,
            max_threshold=input.max_threshold,
            step_size=input.step_size,
            time_window=input.time_window,
            min_replicas=input.min_replicas,
            max_replicas=input.max_replicas,
            prometheus_query_preset_id=input.prometheus_query_preset_id,
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
        scope: AutoScalingRuleSearchScope,
        input: SearchAutoScalingRulesInput,
    ) -> SearchAutoScalingRulesPayload:
        """Search auto-scaling rules scoped to a specific deployment."""
        querier = self._build_auto_scaling_rule_querier(input, scope=scope)
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
                if not isinstance(input.min_threshold, Sentinel) and input.min_threshold is not None
                else OptionalState.nop()
            ),
            max_threshold=(
                OptionalState.update(input.max_threshold)
                if not isinstance(input.max_threshold, Sentinel) and input.max_threshold is not None
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
                if not isinstance(input.min_replicas, Sentinel) and input.min_replicas is not None
                else OptionalState.nop()
            ),
            max_replicas=(
                OptionalState.update(input.max_replicas)
                if not isinstance(input.max_replicas, Sentinel) and input.max_replicas is not None
                else OptionalState.nop()
            ),
            prometheus_query_preset_id=(
                OptionalState.update(input.prometheus_query_preset_id)
                if not isinstance(input.prometheus_query_preset_id, Sentinel)
                and input.prometheus_query_preset_id is not None
                else OptionalState.nop()
            ),
        )
        action_result = (
            await self._processors.deployment.update_auto_scaling_rule.wait_for_complete(
                UpdateAutoScalingRuleAction(auto_scaling_rule_id=input.id, modifier=modifier)
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

    async def bulk_delete_rules(
        self, input: BulkDeleteAutoScalingRulesInput
    ) -> BulkDeleteAutoScalingRulesPayload:
        """Bulk delete auto-scaling rules."""
        action_result = (
            await self._processors.deployment.bulk_delete_auto_scaling_rules.wait_for_complete(
                BulkDeleteAutoScalingRulesAction(auto_scaling_rule_ids=input.ids)
            )
        )
        return BulkDeleteAutoScalingRulesPayload(ids=action_result.deleted_ids)

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
                if rolling is not None:
                    strategy_spec = RollingUpdateSpec(
                        max_surge=rolling.max_surge,
                        max_unavailable=rolling.max_unavailable,
                    )
                else:
                    strategy_spec = RollingUpdateSpec()
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
        input: AddRevisionGQLInputDTO,
    ) -> AddRevisionPayload:
        """Add a new model revision to a deployment."""
        mounts_creator = VFolderMountsCreator(
            model_vfolder_id=input.model_mount_config.vfolder_id,
            model_definition_path=input.model_mount_config.definition_path,
            model_mount_destination=input.model_mount_config.mount_destination,
            extra_mounts=[
                MountInfo(
                    vfolder_id=m.vfolder_id,
                    kernel_path=PurePosixPath(m.mount_destination) if m.mount_destination else None,
                )
                for m in (input.extra_mounts or [])
            ],
        )
        adder = ModelRevisionCreator(
            image_id=input.image.id,
            resource_spec=ResourceSpec(
                cluster_mode=input.cluster_config.mode,
                cluster_size=input.cluster_config.size,
                resource_slots={
                    e.resource_type: e.quantity
                    for e in input.resource_config.resource_slots.entries
                },
                resource_opts={e.name: e.value for e in input.resource_config.resource_opts.entries}
                if input.resource_config.resource_opts
                else None,
            ),
            mounts=mounts_creator,
            execution=ExecutionSpec(
                runtime_variant=RuntimeVariant(input.model_runtime_config.runtime_variant),
                environ={e.name: e.value for e in input.model_runtime_config.environ.entries}
                if input.model_runtime_config.environ
                else None,
                inference_runtime_config=input.model_runtime_config.inference_runtime_config,
            ),
            model_definition=input.model_definition,
            revision_preset_id=input.revision_preset_id,
            auto_activate=input.auto_activate,
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
        scope: RevisionSearchScope,
        input: AdminSearchRevisionsInput,
    ) -> AdminSearchRevisionsPayload:
        """Search model revisions scoped to a specific deployment."""
        querier = self._build_revision_querier(input, scope=scope)
        action_result = await self._processors.deployment.search_revisions.wait_for_complete(
            SearchRevisionsAction(querier=querier)
        )
        return AdminSearchRevisionsPayload(
            items=[self._revision_data_to_dto(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def admin_search_revisions(
        self,
        input: AdminSearchRevisionsInput,
    ) -> AdminSearchRevisionsPayload:
        """Search model revisions without scope (admin, all deployments)."""
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
    # Revision resource slot operations
    # ------------------------------------------------------------------

    async def search_revision_resource_slots(
        self,
        revision_id: UUID,
        input: SearchAllocatedResourceSlotsInput,
    ) -> SearchAllocatedResourceSlotsPayload:
        """Search resource slots allocated to a deployment revision."""
        querier = self._build_revision_resource_slot_querier(input, revision_id=revision_id)
        action_result = (
            await self._processors.deployment.search_revision_resource_slots.wait_for_complete(
                SearchRevisionResourceSlotsAction(
                    revision_id=revision_id,
                    querier=querier,
                )
            )
        )
        return SearchAllocatedResourceSlotsPayload(
            items=[
                AllocatedResourceSlotNode(slot_name=slot_name, quantity=quantity)
                for slot_name, quantity in action_result.items
            ],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    # ------------------------------------------------------------------
    # Route operations
    # ------------------------------------------------------------------

    async def search_routes(
        self,
        scope: RouteSearchScope,
        input: SearchRoutesInput,
    ) -> SearchRoutesPayload:
        """Search routes scoped to a specific deployment."""
        querier = self._build_route_querier(input, scope=scope)
        action_result = await self._processors.deployment.search_routes.wait_for_complete(
            SearchRoutesAction(querier=querier)
        )
        return SearchRoutesPayload(
            items=[self._route_info_to_dto(item) for item in action_result.routes],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    # ------------------------------------------------------------------
    # Replica operations
    # ------------------------------------------------------------------

    async def search_replicas(
        self,
        scope: ReplicaSearchScope,
        input: SearchReplicasInput,
    ) -> SearchReplicasPayload:
        """Search replicas scoped to a specific deployment."""
        querier = self._build_replica_querier(input, scope=scope)
        action_result = await self._processors.deployment.search_replicas.wait_for_complete(
            SearchReplicasAction(querier=querier)
        )
        return SearchReplicasPayload(
            items=[self._replica_data_to_dto(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def admin_search_replicas(
        self,
        input: SearchReplicasInput,
    ) -> SearchReplicasPayload:
        """Search replicas without scope (admin, all deployments)."""
        querier = self._build_replica_querier(input)
        action_result = await self._processors.deployment.search_replicas.wait_for_complete(
            SearchReplicasAction(querier=querier)
        )
        return SearchReplicasPayload(
            items=[self._replica_data_to_dto(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def get_replica(self, replica_id: UUID) -> ReplicaNode | None:
        """Retrieve a single replica by ID."""
        action_result = await self._processors.deployment.get_replica_by_id.wait_for_complete(
            GetReplicaByIdAction(replica_id=replica_id)
        )
        if action_result.data is None:
            return None
        return self._replica_data_to_dto(action_result.data)

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
    # Batch load methods for DataLoader use
    # ------------------------------------------------------------------

    async def batch_load_by_ids(
        self,
        deployment_ids: Sequence[uuid.UUID],
    ) -> list[DeploymentNode | None]:
        """Batch load deployments by ID for DataLoader use.

        Returns DeploymentNode DTOs in the same order as the input deployment_ids list.
        """
        if not deployment_ids:
            return []
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=len(deployment_ids)),
            conditions=[DeploymentConditions.by_ids(deployment_ids)],
        )
        action_result = await self._processors.deployment.search_deployments.wait_for_complete(
            SearchDeploymentsAction(querier=querier)
        )
        deployment_map = {
            data.id: self._deployment_data_to_dto(data) for data in action_result.data
        }
        return [deployment_map.get(deployment_id) for deployment_id in deployment_ids]

    async def batch_load_revisions_by_ids(
        self,
        revision_ids: Sequence[uuid.UUID],
    ) -> list[RevisionNode | None]:
        """Batch load revisions by ID for DataLoader use.

        Returns RevisionNode DTOs in the same order as the input revision_ids list.
        """
        if not revision_ids:
            return []
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=len(revision_ids)),
            conditions=[RevisionConditions.by_ids(revision_ids)],
        )
        action_result = await self._processors.deployment.search_revisions.wait_for_complete(
            SearchRevisionsAction(querier=querier)
        )
        revision_map = {data.id: self._revision_data_to_dto(data) for data in action_result.data}
        return [revision_map.get(revision_id) for revision_id in revision_ids]

    async def batch_load_replicas_by_ids(
        self,
        replica_ids: Sequence[uuid.UUID],
    ) -> list[ReplicaNode | None]:
        """Batch load replicas by ID for DataLoader use.

        Returns ReplicaNode DTOs in the same order as the input replica_ids list.
        """
        if not replica_ids:
            return []
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=len(replica_ids)),
            conditions=[RouteConditions.by_ids(replica_ids)],
        )
        action_result = await self._processors.deployment.search_replicas.wait_for_complete(
            SearchReplicasAction(querier=querier)
        )
        replica_map = {data.id: self._replica_data_to_dto(data) for data in action_result.data}
        return [replica_map.get(replica_id) for replica_id in replica_ids]

    async def batch_load_routes_by_ids(
        self,
        route_ids: Sequence[uuid.UUID],
    ) -> list[RouteNode | None]:
        """Batch load routes by ID for DataLoader use.

        Returns RouteNode DTOs in the same order as the input route_ids list.
        """
        if not route_ids:
            return []
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=len(route_ids)),
            conditions=[RouteConditions.by_ids(route_ids)],
        )
        action_result = await self._processors.deployment.search_routes.wait_for_complete(
            SearchRoutesAction(querier=querier)
        )
        route_map = {
            route.route_id: self._route_info_to_dto(route) for route in action_result.routes
        }
        return [route_map.get(route_id) for route_id in route_ids]

    async def batch_load_access_tokens_by_ids(
        self,
        token_ids: Sequence[uuid.UUID],
    ) -> list[AccessTokenNode | None]:
        """Batch load access tokens by ID for DataLoader use.

        Returns AccessTokenNode DTOs in the same order as the input token_ids list.
        """
        if not token_ids:
            return []
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=len(token_ids)),
            conditions=[AccessTokenConditions.by_ids(token_ids)],
        )
        action_result = await self._processors.deployment.search_access_tokens.wait_for_complete(
            SearchAccessTokensAction(querier=querier)
        )
        token_map = {data.id: self._access_token_data_to_dto(data) for data in action_result.data}
        return [token_map.get(token_id) for token_id in token_ids]

    async def batch_load_auto_scaling_rules_by_ids(
        self,
        rule_ids: Sequence[uuid.UUID],
    ) -> list[AutoScalingRuleNode | None]:
        """Batch load auto-scaling rules by ID for DataLoader use.

        Returns AutoScalingRuleNode DTOs in the same order as the input rule_ids list.
        """
        if not rule_ids:
            return []
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=len(rule_ids)),
            conditions=[AutoScalingRuleConditions.by_ids(rule_ids)],
        )
        action_result = (
            await self._processors.deployment.search_auto_scaling_rules.wait_for_complete(
                SearchAutoScalingRulesAction(querier=querier)
            )
        )
        rule_map = {
            data.id: self._auto_scaling_rule_data_to_dto(data) for data in action_result.data
        }
        return [rule_map.get(rule_id) for rule_id in rule_ids]

    async def batch_load_policies_by_endpoint_ids(
        self,
        endpoint_ids: Sequence[uuid.UUID],
    ) -> list[DeploymentPolicyNode | None]:
        """Batch load deployment policies by endpoint ID for DataLoader use.

        Each endpoint has at most one deployment policy (1:1 relationship).
        Returns DeploymentPolicyNode DTOs in the same order as the input endpoint_ids list.
        """
        if not endpoint_ids:
            return []
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[DeploymentPolicyConditions.by_endpoint_ids(endpoint_ids)],
        )
        action_result = (
            await self._processors.deployment.search_deployment_policies.wait_for_complete(
                SearchDeploymentPoliciesAction(querier=querier)
            )
        )
        policy_map = {data.endpoint: self._policy_data_to_dto(data) for data in action_result.data}
        return [policy_map.get(endpoint_id) for endpoint_id in endpoint_ids]

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
                    in_factory=DeploymentConditions.by_name_in,
                )
                if condition is not None:
                    conditions.append(condition)
            if f.open_to_public is not None:
                conditions.append(DeploymentConditions.by_open_to_public(f.open_to_public))
        orders: list[QueryOrder] = (
            self._convert_deployment_orders(input.order) if input.order else []
        )
        return self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_get_deployment_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

    def _build_revision_querier(
        self,
        input: AdminSearchRevisionsInput,
        scope: RevisionSearchScope | None = None,
    ) -> BatchQuerier:
        conditions: list[QueryCondition] = []
        if scope is not None:
            conditions.append(RevisionConditions.by_deployment_id(scope.deployment_id))
        if input.filter:
            f = input.filter
            if scope is None and f.deployment_id is not None:
                conditions.append(RevisionConditions.by_deployment_id(f.deployment_id))
            if f.name is not None:
                condition = self.convert_string_filter(
                    f.name,
                    contains_factory=RevisionConditions.by_name_contains,
                    equals_factory=RevisionConditions.by_name_equals,
                    starts_with_factory=RevisionConditions.by_name_starts_with,
                    ends_with_factory=RevisionConditions.by_name_ends_with,
                    in_factory=RevisionConditions.by_name_in,
                )
                if condition is not None:
                    conditions.append(condition)
        orders: list[QueryOrder] = self._convert_revision_orders(input.order) if input.order else []
        return self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_get_revision_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

    def _build_route_querier(
        self,
        input: SearchRoutesInput,
        scope: RouteSearchScope | None = None,
    ) -> BatchQuerier:
        conditions: list[QueryCondition] = []
        if scope is not None:
            conditions.append(RouteConditions.by_endpoint_id(scope.deployment_id))
        if input.filter:
            f = input.filter
            if scope is None and f.deployment_id is not None:
                conditions.append(RouteConditions.by_endpoint_id(f.deployment_id))
            if f.status is not None:
                conditions.append(
                    RouteConditions.by_statuses([ManagerRouteStatus(s.value) for s in f.status])
                )
            if f.health_status is not None:
                conditions.append(
                    RouteConditions.by_health_statuses([
                        ManagerRouteHealthStatus(s.value) for s in f.health_status
                    ])
                )
            if f.traffic_status is not None:
                conditions.append(
                    RouteConditions.by_traffic_statuses([
                        ManagerRouteTrafficStatus(s.value) for s in f.traffic_status
                    ])
                )
        orders: list[QueryOrder] = self._convert_route_orders(input.order) if input.order else []
        return self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_get_route_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

    def _build_access_token_querier(
        self,
        input: SearchAccessTokensInput,
        scope: AccessTokenSearchScope | None = None,
    ) -> BatchQuerier:
        conditions: list[QueryCondition] = []
        if scope is not None:
            conditions.append(AccessTokenConditions.by_endpoint_id(scope.deployment_id))
        elif input.filter and input.filter.deployment_id is not None:
            conditions.append(AccessTokenConditions.by_endpoint_id(input.filter.deployment_id))
        orders: list[QueryOrder] = (
            [
                AccessTokenOrders.created_at(ascending=o.direction == OrderDirection.ASC)
                for o in input.order
            ]
            if input.order
            else []
        )
        return self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_get_access_token_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

    def _build_auto_scaling_rule_querier(
        self,
        input: SearchAutoScalingRulesInput,
        scope: AutoScalingRuleSearchScope | None = None,
    ) -> BatchQuerier:
        conditions: list[QueryCondition] = []
        if scope is not None:
            conditions.append(AutoScalingRuleConditions.by_deployment_id(scope.deployment_id))
        elif input.filter and input.filter.deployment_id is not None:
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
        return self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_get_auto_scaling_rule_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

    def _build_policy_querier(self, input: SearchDeploymentPoliciesInput) -> BatchQuerier:
        conditions: list[QueryCondition] = []
        if input.filter and input.filter.deployment_id is not None:
            conditions.append(
                DeploymentPolicyConditions.by_endpoint_ids([input.filter.deployment_id])
            )
        return self._build_querier(
            conditions=conditions,
            orders=[],
            pagination_spec=_get_deployment_policy_pagination_spec(),
            limit=input.limit,
            offset=input.offset,
        )

    def _build_replica_querier(
        self,
        input: SearchReplicasInput,
        scope: ReplicaSearchScope | None = None,
    ) -> BatchQuerier:
        conditions: list[QueryCondition] = []
        if scope is not None:
            conditions.append(RouteConditions.by_endpoint_id(scope.deployment_id))
        if input.filter:
            f = input.filter
            if scope is None and f.deployment_id is not None:
                conditions.append(RouteConditions.by_endpoint_id(f.deployment_id))
            if f.status is not None:
                st = f.status
                if st.equals is not None:
                    conditions.append(
                        RouteConditions.by_status_equals(ManagerRouteStatus(st.equals.value))
                    )
                if st.in_ is not None:
                    conditions.append(
                        RouteConditions.by_statuses([ManagerRouteStatus(s.value) for s in st.in_])
                    )
            if f.traffic_status is not None:
                ts = f.traffic_status
                if ts.equals is not None:
                    conditions.append(
                        RouteConditions.by_traffic_status_equals(
                            ManagerRouteTrafficStatus(ts.equals.value)
                        )
                    )
                if ts.in_ is not None:
                    conditions.append(
                        RouteConditions.by_traffic_statuses([
                            ManagerRouteTrafficStatus(s.value) for s in ts.in_
                        ])
                    )
        orders: list[QueryOrder] = self._convert_replica_orders(input.order) if input.order else []
        return self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_get_replica_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

    def _build_revision_resource_slot_querier(
        self,
        input: SearchAllocatedResourceSlotsInput,
        revision_id: UUID,
    ) -> BatchQuerier:
        conditions: list[QueryCondition] = [
            RevisionResourceSlotConditions.by_revision_id(revision_id),
        ]
        if input.filter:
            conditions.extend(
                self._convert_allocated_slot_filter(
                    input.filter,
                    RevisionResourceSlotConditions,
                )
            )
        orders: list[QueryOrder] = (
            [resolve_allocated_slot_revision_order(o.field, o.direction) for o in input.order]
            if input.order
            else []
        )
        return self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_get_revision_resource_slot_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

    def _convert_allocated_slot_filter(
        self,
        filter_: AllocatedResourceSlotFilter,
        conditions_cls: type[RevisionResourceSlotConditions],
    ) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter_.slot_name is not None:
            cond = self.convert_string_filter(
                filter_.slot_name,
                contains_factory=conditions_cls.by_slot_name_contains,
                equals_factory=conditions_cls.by_slot_name_equals,
                starts_with_factory=conditions_cls.by_slot_name_starts_with,
                ends_with_factory=conditions_cls.by_slot_name_ends_with,
                in_factory=conditions_cls.by_slot_name_in,
            )
            if cond is not None:
                conditions.append(cond)
        if filter_.AND:
            for sub in filter_.AND:
                conditions.extend(self._convert_allocated_slot_filter(sub, conditions_cls))
        if filter_.OR:
            or_conds: list[QueryCondition] = []
            for sub in filter_.OR:
                or_conds.extend(self._convert_allocated_slot_filter(sub, conditions_cls))
            if or_conds:
                conditions.append(combine_conditions_or(or_conds))
        return conditions

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

    @staticmethod
    def _convert_replica_orders(orders: list[ReplicaOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for o in orders:
            ascending = o.direction == OrderDirection.ASC
            match o.field:
                case ReplicaOrderField.CREATED_AT:
                    result.append(RouteOrders.created_at(ascending))
                case ReplicaOrderField.ID:
                    result.append(RouteOrders.id(ascending))
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
                rolling_update=rolling,
                blue_green=blue_green,
            )
        return DeploymentNode(
            id=data.id,
            metadata=DeploymentMetadataInfoDTO(
                project_id=str(data.metadata.project_id),
                domain_name=data.metadata.domain_name,
                name=data.metadata.name,
                status=data.metadata.status,
                tags=data.metadata.tags,
                created_at=data.metadata.created_at,
                updated_at=data.metadata.updated_at,
            ),
            network_access=DeploymentNetworkAccessInfoDTO(
                endpoint_url=data.network_access.url,
                preferred_domain_name=data.network_access.preferred_domain_name,
                open_to_public=data.network_access.open_to_public,
            ),
            replica_state=ReplicaStateInfo(
                desired_replica_count=data.replica_state.desired_replica_count,
                replica_ids=data.replica_state.replica_ids,
            ),
            default_deployment_strategy=DeploymentStrategyInfoDTO(
                type=data.default_deployment_strategy,
            ),
            created_user_id=data.created_user_id,
            current_revision_id=data.revision.id if data.revision is not None else None,
            policy=policy_info,
        )

    @staticmethod
    def _revision_data_to_dto(data: ModelRevisionData) -> RevisionNode:
        environ_dto: EnvironmentVariablesInfoDTO | None = None
        if data.model_runtime_config.environ:
            environ_dto = EnvironmentVariablesInfoDTO(
                entries=[
                    EnvironmentVariableEntryInfoDTO(name=k, value=str(v))
                    for k, v in data.model_runtime_config.environ.items()
                ]
            )
        model_mount_config_dto: ModelMountConfigInfoDTO | None = None
        if data.model_mount_config.vfolder_id and data.model_mount_config.mount_destination:
            model_mount_config_dto = ModelMountConfigInfoDTO(
                vfolder_id=str(data.model_mount_config.vfolder_id),
                mount_destination=data.model_mount_config.mount_destination,
                definition_path=data.model_mount_config.definition_path,
            )
        return RevisionNode(
            id=data.id,
            name=data.name,
            image_id=data.image_id,
            cluster_config=ClusterConfigInfoDTO(
                mode=data.cluster_config.mode.name,
                size=data.cluster_config.size,
            ),
            resource_config=ResourceConfigInfoDTO(
                resource_group_name=data.resource_config.resource_group_name,
                resource_opts=(
                    ResourceOptsInfoDTO(
                        entries=[
                            ResourceOptsEntryInfoDTO(name=k, value=str(v))
                            for k, v in data.resource_config.resource_opts.items()
                        ]
                    )
                    if data.resource_config.resource_opts
                    else None
                ),
            ),
            model_runtime_config=ModelRuntimeConfigInfoDTO(
                runtime_variant=str(data.model_runtime_config.runtime_variant),
                inference_runtime_config=(
                    dict(data.model_runtime_config.inference_runtime_config)
                    if data.model_runtime_config.inference_runtime_config
                    else None
                ),
                environ=environ_dto,
            ),
            model_mount_config=model_mount_config_dto,
            model_definition=(
                ModelDefinitionInfoDTO.model_validate(
                    data.model_definition.model_dump(by_alias=False)
                )
                if data.model_definition is not None
                else None
            ),
            created_at=data.created_at,
            extra_mounts=[
                ExtraVFolderMountGQLDTO(
                    vfolder_id=str(m.vfolder_id),
                    mount_destination=m.mount_destination,
                )
                for m in data.extra_vfolder_mounts
            ],
        )

    @staticmethod
    def _route_info_to_dto(data: RouteInfo) -> RouteNode:
        return RouteNode(
            id=data.route_id,
            deployment_id=data.endpoint_id,
            session_id=str(data.session_id) if data.session_id is not None else None,
            status=RouteStatus(data.status.value),
            health_status=RouteHealthStatus(data.health_status.value),
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
            expires_at=data.expires_at,
            created_at=data.created_at,
        )

    @staticmethod
    def _auto_scaling_rule_data_to_dto(
        data: ModelDeploymentAutoScalingRuleData,
    ) -> AutoScalingRuleNode:
        return AutoScalingRuleNode(
            id=data.id,
            deployment_id=data.model_deployment_id,
            metric_source=data.metric_source.name,
            metric_name=data.metric_name,
            min_threshold=data.min_threshold,
            max_threshold=data.max_threshold,
            step_size=data.step_size,
            time_window=data.time_window,
            min_replicas=data.min_replicas,
            max_replicas=data.max_replicas,
            prometheus_query_preset_id=data.prometheus_query_preset_id,
            created_at=data.created_at,
            last_triggered_at=data.last_triggered_at,
        )

    @staticmethod
    def _policy_data_to_dto(data: DeploymentPolicyData) -> DeploymentPolicyNode:
        strategy_spec: RollingUpdateStrategySpecInfo | BlueGreenStrategySpecInfo
        if isinstance(data.strategy_spec, RollingUpdateSpec):
            strategy_spec = RollingUpdateStrategySpecInfo(
                strategy=data.strategy,
                max_surge=data.strategy_spec.max_surge,
                max_unavailable=data.strategy_spec.max_unavailable,
            )
        else:
            strategy_spec = BlueGreenStrategySpecInfo(
                strategy=data.strategy,
                auto_promote=data.strategy_spec.auto_promote,
                promote_delay_seconds=data.strategy_spec.promote_delay_seconds,
            )
        return DeploymentPolicyNode(
            id=data.id,
            deployment_id=data.endpoint,
            strategy_spec=strategy_spec,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )

    @staticmethod
    def _replica_data_to_dto(data: ModelReplicaData) -> ReplicaNode:
        return ReplicaNode(
            id=data.id,
            revision_id=data.revision_id,
            session_id=data.session_id,
            readiness_status=data.readiness_status,
            liveness_status=data.liveness_status,
            activeness_status=data.activeness_status,
            created_at=data.created_at,
        )
