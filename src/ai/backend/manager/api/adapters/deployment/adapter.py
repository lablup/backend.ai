"""Deployment adapter bridging DTOs and Processors."""

from __future__ import annotations

import uuid
from collections.abc import Collection, Sequence
from decimal import Decimal
from functools import lru_cache
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors
    from ai.backend.manager.sokovan.deployment.coordinator import DeploymentCoordinator

from ai.backend.common.api_handlers import Sentinel
from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.model_deployment.types import (
    DeploymentStrategy,
    ModelDeploymentStatus,
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
from ai.backend.common.dto.manager.v2.common import ResourceSlotEntryInfo, ResourceSlotInfo
from ai.backend.common.dto.manager.v2.deployment.request import (
    AccessTokenFilter,
    ActivateRevisionInput,
    AddRevisionInput,
    AddRevisionOptions,
    AdminSearchRevisionsInput,
    AutoScalingRuleFilter,
    BulkDeleteAccessTokensInput,
    CreateAccessTokenInput,
    CreateDeploymentInput,
    DeleteAccessTokenInput,
    DeleteDeploymentInput,
    DeploymentFilter,
    DeploymentOrder,
    ReplaceDeploymentOptionsInput,
    ReplicaFilter,
    ReplicaOrder,
    RevisionFilter,
    RevisionOrder,
    RouteFilter,
    RouteOrder,
    SearchAccessTokensInput,
    SearchAutoScalingRulesInput,
    SearchDeploymentPoliciesInput,
    SearchDeploymentsInput,
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
    AdminRefreshDeploymentRevisionsPayload,
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
    ReplaceDeploymentOptionsPayload,
    ReplicaNode,
    RevisionNode,
    RevisionRefreshResultInfo,
    RouteNode,
    SearchAccessTokensPayload,
    SearchAutoScalingRulesPayload,
    SearchDeploymentPoliciesPayload,
    SearchDeploymentsPayload,
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
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.manager.api.adapter_options.deployment.options import (
    deployment_options_from_input,
    deployment_options_to_info,
)
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
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
    combine_conditions_and,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.deployment.types import (
    ProjectDeploymentSearchScope,
    UserDeploymentSearchScope,
)
from ai.backend.manager.repositories.deployment.updaters import (
    DeploymentMetadataUpdaterSpec,
    DeploymentNetworkSpecUpdaterSpec,
    DeploymentUpdaterSpec,
    ReplicaSpecUpdaterSpec,
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
from ai.backend.manager.services.deployment.actions.admin_search_deployments import (
    AdminSearchDeploymentsAction,
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
from ai.backend.manager.services.deployment.actions.refresh_deployment_revisions import (
    RefreshDeploymentRevisionsAction,
)
from ai.backend.manager.services.deployment.actions.replace_deployment_options import (
    ReplaceDeploymentOptionsAction,
)
from ai.backend.manager.services.deployment.actions.revision_operations import (
    ActivateRevisionAction,
)
from ai.backend.manager.services.deployment.actions.route.search_routes import SearchRoutesAction
from ai.backend.manager.services.deployment.actions.route.update_route_traffic_status import (
    UpdateRouteTrafficStatusAction,
)
from ai.backend.manager.services.deployment.actions.search_project_deployments import (
    SearchProjectDeploymentsAction,
)
from ai.backend.manager.services.deployment.actions.search_replicas import SearchReplicasAction
from ai.backend.manager.services.deployment.actions.search_user_deployments import (
    SearchUserDeploymentsAction,
)
from ai.backend.manager.services.deployment.actions.sync_replicas import SyncReplicaAction
from ai.backend.manager.services.deployment.actions.update_deployment import UpdateDeploymentAction
from ai.backend.manager.types import OptionalState, TriState

DEFAULT_PAGINATION_LIMIT = 10


def _tristate_from_input[T](value: T | Sentinel | None) -> TriState[T]:
    """Map a DTO-style optional value (Sentinel / None / value) to TriState.

    - ``Sentinel`` → NOP (field was not provided; leave the attribute unchanged)
    - ``None`` → NULLIFY (field was provided as ``null``; clear the attribute)
    - otherwise → UPDATE (replace with the given value)
    """
    if isinstance(value, Sentinel):
        return TriState[T].nop()
    if value is None:
        return TriState[T].nullify()
    return TriState[T].update(value)


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


_STATUS_TO_LIFECYCLE: dict[ModelDeploymentStatus, list[EndpointLifecycle]] = {
    ModelDeploymentStatus.PENDING: [EndpointLifecycle.PENDING, EndpointLifecycle.CREATED],
    ModelDeploymentStatus.SCALING: [EndpointLifecycle.SCALING],
    ModelDeploymentStatus.DEPLOYING: [EndpointLifecycle.DEPLOYING],
    ModelDeploymentStatus.READY: [EndpointLifecycle.READY],
    ModelDeploymentStatus.STOPPING: [EndpointLifecycle.DESTROYING],
    ModelDeploymentStatus.STOPPED: [EndpointLifecycle.DESTROYED],
}


def _status_to_lifecycles(status: ModelDeploymentStatus) -> list[EndpointLifecycle]:
    return _STATUS_TO_LIFECYCLE.get(status, [])


def _to_common_route_status(value: ManagerRouteStatus) -> RouteStatus:
    match value:
        case ManagerRouteStatus.PROVISIONING:
            return RouteStatus.PROVISIONING
        case ManagerRouteStatus.RUNNING:
            return RouteStatus.RUNNING
        case ManagerRouteStatus.TERMINATING:
            return RouteStatus.TERMINATING
        case ManagerRouteStatus.TERMINATED:
            return RouteStatus.TERMINATED
        case ManagerRouteStatus.FAILED_TO_START:
            return RouteStatus.FAILED_TO_START


def _to_common_route_traffic_status(value: ManagerRouteTrafficStatus) -> RouteTrafficStatus:
    match value:
        case ManagerRouteTrafficStatus.ACTIVE:
            return RouteTrafficStatus.ACTIVE
        case ManagerRouteTrafficStatus.INACTIVE:
            return RouteTrafficStatus.INACTIVE


def _to_common_route_health_status(value: ManagerRouteHealthStatus) -> RouteHealthStatus:
    match value:
        case ManagerRouteHealthStatus.NOT_CHECKED:
            return RouteHealthStatus.NOT_CHECKED
        case ManagerRouteHealthStatus.HEALTHY:
            return RouteHealthStatus.HEALTHY
        case ManagerRouteHealthStatus.UNHEALTHY:
            return RouteHealthStatus.UNHEALTHY
        case ManagerRouteHealthStatus.DEGRADED:
            return RouteHealthStatus.DEGRADED


def _statuses_to_lifecycles(
    statuses: Collection[ModelDeploymentStatus],
) -> list[EndpointLifecycle]:
    result: list[EndpointLifecycle] = []
    for s in statuses:
        result.extend(_status_to_lifecycles(s))
    return result


class DeploymentAdapter(BaseAdapter):
    """Adapter for deployment domain operations."""

    def __init__(
        self,
        processors: Processors,
        deployment_coordinator: DeploymentCoordinator,
    ) -> None:
        super().__init__(processors)
        # ``deployment_coordinator`` is the authoritative source for the
        # live set of registered handler names; we consult it when
        # validating ``DeploymentOptions.handler_options.by_handler`` keys so an
        # unknown handler surfaces as a 400 instead of a silently stored,
        # never-dispatched entry.
        self._deployment_coordinator = deployment_coordinator

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
        if initial_revision is not None:
            mounts_creator = VFolderMountsCreator(
                model_vfolder_id=initial_revision.model_mount_config.vfolder_id,
                model_definition_path=initial_revision.model_mount_config.definition_path,
                model_mount_destination=initial_revision.model_mount_config.mount_destination,
                extra_mounts=[
                    MountInfo(
                        vfolder_id=m.vfolder_id,
                        mount_destination=m.mount_destination,
                        mount_perm=m.mount_perm,
                        subpath=m.subpath,
                    )
                    for m in (initial_revision.extra_mounts or [])
                ],
                vfolder_subpath=initial_revision.model_mount_config.subpath,
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
                model_definition=initial_revision.model_definition.to_draft()
                if initial_revision.model_definition is not None
                else None,
                revision_preset_id=initial_revision.revision_preset_id,
                execution=ExecutionSpec(
                    runtime_variant_id=initial_revision.model_runtime_config.runtime_variant_id,
                    environ={
                        e.name: e.value
                        for e in initial_revision.model_runtime_config.environ.entries
                    }
                    if initial_revision.model_runtime_config.environ
                    else None,
                ),
            )
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
                resource_group=meta.resource_group_name,
                created_user=created_user_id,
                session_owner=created_user_id,
                created_at=None,
                revision_history_limit=10,
                tag=",".join(meta.tags) if meta.tags else None,
            ),
            replica_spec=ReplicaSpec(replica_count=input.replica_count),
            network=DeploymentNetworkSpec(
                open_to_public=input.network_access.open_to_public,
                preferred_domain_name=input.network_access.preferred_domain_name,
            ),
            model_revision=model_revision_creator,
            policy=policy,
        )
        action_result = await self._processors.deployment.create_deployment.wait_for_complete(
            CreateDeploymentAction(
                creator=creator,
                auto_activate=initial_revision.auto_activate
                if initial_revision is not None
                else False,
            )
        )
        return CreateDeploymentPayload(deployment=self._deployment_data_to_dto(action_result.data))

    async def admin_search(
        self,
        input: SearchDeploymentsInput,
    ) -> SearchDeploymentsPayload:
        """Search deployments (admin, no scope)."""
        querier = self._build_deployment_querier(input)
        action_result = (
            await self._processors.deployment_admin.admin_search_deployments.wait_for_complete(
                AdminSearchDeploymentsAction(querier=querier)
            )
        )
        return SearchDeploymentsPayload(
            items=[self._deployment_data_to_dto(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def my_search(
        self,
        input: SearchDeploymentsInput,
    ) -> SearchDeploymentsPayload:
        """Search deployments owned by the current user."""
        user = current_user()
        if user is None:
            raise RuntimeError("No authenticated user in context")
        scope = UserDeploymentSearchScope(user_id=user.user_id)
        conditions: list[QueryCondition] = []
        if input.filter:
            conditions.extend(self._convert_deployment_filter(input.filter))
        orders: list[QueryOrder] = (
            self._convert_deployment_orders(input.order) if input.order else []
        )
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
        )
        action_result = await self._processors.deployment.search_user_deployments.wait_for_complete(
            SearchUserDeploymentsAction(scope=scope, querier=querier)
        )
        return SearchDeploymentsPayload(
            items=[self._deployment_data_to_dto(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def project_search(
        self,
        project_id: UUID,
        input: SearchDeploymentsInput,
    ) -> SearchDeploymentsPayload:
        """Search deployments within a specific project."""
        scope = ProjectDeploymentSearchScope(project_id=project_id)
        conditions: list[QueryCondition] = []
        if input.filter:
            conditions.extend(self._convert_deployment_filter(input.filter))
        orders: list[QueryOrder] = (
            self._convert_deployment_orders(input.order) if input.order else []
        )
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
        )
        action_result = (
            await self._processors.deployment.search_project_deployments.wait_for_complete(
                SearchProjectDeploymentsAction(scope=scope, querier=querier)
            )
        )
        return SearchDeploymentsPayload(
            items=[self._deployment_data_to_dto(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def get(self, deployment_id: DeploymentID) -> DeploymentNode:
        """Retrieve a single deployment by ID."""
        action_result = await self._processors.deployment.get_deployment_by_id.wait_for_complete(
            GetDeploymentByIdAction(deployment_id=deployment_id)
        )
        return self._deployment_data_to_dto(action_result.data)

    async def get_current_revision(self, deployment_id: DeploymentID) -> RevisionNode:
        """Retrieve the current active revision of a deployment."""
        deployment = await self.get(deployment_id)
        if deployment.current_revision_id is None:
            raise DeploymentRevisionNotFound(f"Deployment {deployment_id} has no current revision")
        return await self.get_revision(DeploymentRevisionID(deployment.current_revision_id))

    async def update(
        self,
        input: UpdateDeploymentInput,
        deployment_id: DeploymentID,
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
        if input.replica_count is not None:
            replica_spec = ReplicaSpecUpdaterSpec(
                replica_count=OptionalState.update(input.replica_count),
            )
        network_spec: DeploymentNetworkSpecUpdaterSpec | None = None
        if input.open_to_public is not None:
            network_spec = DeploymentNetworkSpecUpdaterSpec(
                open_to_public=OptionalState.from_graphql(input.open_to_public),
            )
        spec = DeploymentUpdaterSpec(
            metadata=metadata_spec,
            replica_spec=replica_spec,
            network=network_spec,
        )
        updater: Updater[EndpointRow] = Updater(spec=spec, pk_value=deployment_id)
        action_result = await self._processors.deployment.update_deployment.wait_for_complete(
            UpdateDeploymentAction(updater=updater)
        )
        return UpdateDeploymentPayload(deployment=self._deployment_data_to_dto(action_result.data))

    async def replace_options(
        self,
        deployment_id: DeploymentID,
        input: ReplaceDeploymentOptionsInput,
    ) -> ReplaceDeploymentOptionsPayload:
        """Fully replace the ``options`` surface of a deployment.

        Accepts the REST/GQL DTO input, converts to the domain
        :class:`DeploymentOptions` (duplicate or unknown handler names
        are rejected inside :func:`deployment_options_from_input`
        against the coordinator's live registration), dispatches the
        :class:`ReplaceDeploymentOptionsAction`, and returns only the
        refreshed options surface (the repository path uses ``UPDATE ...
        RETURNING`` and does not read the surrounding deployment node).
        """
        options = deployment_options_from_input(
            input.options,
            valid_handler_names=frozenset(
                h.name() for h in self._deployment_coordinator.registered_handlers()
            ),
        )
        action_result = (
            await self._processors.deployment.replace_deployment_options.wait_for_complete(
                ReplaceDeploymentOptionsAction(
                    deployment_id=deployment_id,
                    options=options,
                )
            )
        )
        return ReplaceDeploymentOptionsPayload(
            deployment_id=action_result.deployment_id,
            options=deployment_options_to_info(action_result.options),
        )

    async def sync_replicas(self, input: SyncReplicaInput) -> SyncReplicaPayload:
        """Force sync replica information for a deployment."""
        await self._processors.deployment.sync_replicas.wait_for_complete(
            SyncReplicaAction(deployment_id=DeploymentID(input.model_deployment_id))
        )
        return SyncReplicaPayload(success=True)

    async def activate_revision(self, input: ActivateRevisionInput) -> ActivateRevisionPayload:
        """Activate a specific revision as the current revision."""
        action_result = await self._processors.deployment.activate_revision.wait_for_complete(
            ActivateRevisionAction(
                deployment_id=DeploymentID(input.deployment_id),
                revision_id=DeploymentRevisionID(input.revision_id),
            )
        )
        return ActivateRevisionPayload(
            deployment=self._deployment_data_to_dto(action_result.deployment),
            previous_revision_id=action_result.previous_revision_id,
            activated_revision_id=action_result.activated_revision_id,
            deployment_policy=self._policy_data_to_dto(action_result.deployment_policy),
        )

    async def admin_refresh_deployment_revisions(
        self,
    ) -> AdminRefreshDeploymentRevisionsPayload:
        """Create and activate a fresh revision for every active deployment."""
        action_result = (
            await self._processors.deployment.admin_refresh_deployment_revisions.wait_for_complete(
                RefreshDeploymentRevisionsAction()
            )
        )
        return AdminRefreshDeploymentRevisionsPayload(
            results=[
                RevisionRefreshResultInfo(
                    deployment_id=r.deployment_id,
                    new_revision_id=r.new_revision_id,
                    success=r.success,
                    failure_reason=r.failure_reason,
                )
                for r in action_result.results
            ]
        )

    async def delete(self, input: DeleteDeploymentInput) -> DeleteDeploymentPayload:
        """Delete a deployment."""
        await self._processors.deployment.destroy_deployment.wait_for_complete(
            DestroyDeploymentAction(deployment_id=DeploymentID(input.id))
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
            model_deployment_id=DeploymentID(input.model_deployment_id),
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
            min_threshold=_tristate_from_input(input.min_threshold),
            max_threshold=_tristate_from_input(input.max_threshold),
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
            min_replicas=_tristate_from_input(input.min_replicas),
            max_replicas=_tristate_from_input(input.max_replicas),
            prometheus_query_preset_id=_tristate_from_input(input.prometheus_query_preset_id),
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

    async def get_policy(self, deployment_id: DeploymentID) -> GetDeploymentPolicyPayload:
        """Retrieve a deployment policy by deployment ID."""
        action_result = await self._processors.deployment.get_deployment_policy.wait_for_complete(
            GetDeploymentPolicyAction(deployment_id=deployment_id)
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
        input: AddRevisionInput,
        options: AddRevisionOptions,
    ) -> AddRevisionPayload:
        """Add a new model revision to a deployment.

        Every sub-config on ``AddRevisionInput`` is optional. A
        missing sub-config flows through as ``None`` and is filled by
        the merge chain in ``DeploymentController.add_revision`` (preset,
        runtime variant baseline, vfolder config files, existing
        revision) or by the column server-defaults at DB write time.
        """
        extra_mounts = [
            MountInfo(
                vfolder_id=m.vfolder_id,
                mount_destination=m.mount_destination,
                mount_perm=m.mount_perm,
                subpath=m.subpath,
            )
            for m in (input.extra_mounts or [])
        ]

        mounts_creator = VFolderMountsCreator(
            model_vfolder_id=input.model_mount_config.vfolder_id,
            model_definition_path=input.model_mount_config.definition_path,
            model_mount_destination=input.model_mount_config.mount_destination,
            extra_mounts=extra_mounts,
            vfolder_subpath=input.model_mount_config.subpath,
        )

        image_id = input.image.id if input.image is not None else None

        resource_spec = None
        if input.cluster_config is not None and input.resource_config is not None:
            resource_opts = (
                {e.name: e.value for e in input.resource_config.resource_opts.entries}
                if input.resource_config.resource_opts
                else None
            )
            resource_spec = ResourceSpec(
                cluster_mode=input.cluster_config.mode,
                cluster_size=input.cluster_config.size,
                resource_slots={
                    e.resource_type: e.quantity
                    for e in input.resource_config.resource_slots.entries
                },
                resource_opts=resource_opts,
            )

        execution = None
        if input.model_runtime_config is not None:
            environ = (
                {e.name: e.value for e in input.model_runtime_config.environ.entries}
                if input.model_runtime_config.environ
                else None
            )
            execution = ExecutionSpec(
                runtime_variant_id=input.model_runtime_config.runtime_variant_id,
                environ=environ,
            )

        model_definition = (
            input.model_definition.to_draft() if input.model_definition is not None else None
        )

        adder = ModelRevisionCreator(
            image_id=image_id,
            resource_spec=resource_spec,
            mounts=mounts_creator,
            execution=execution,
            model_definition=model_definition,
            revision_preset_id=input.revision_preset_id,
        )
        action_result = await self._processors.deployment.add_model_revision.wait_for_complete(
            AddModelRevisionAction(
                model_deployment_id=DeploymentID(input.deployment_id),
                adder=adder,
                auto_activate=options.auto_activate,
            )
        )
        return AddRevisionPayload(revision=self._revision_data_to_dto(action_result.revision))

    async def get_revision(self, revision_id: DeploymentRevisionID) -> RevisionNode:
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
        revision_id: DeploymentRevisionID,
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
        deployment_ids: Sequence[DeploymentID],
    ) -> list[DeploymentNode | None]:
        """Batch load deployments by ID for DataLoader use.

        Routed through ``admin_search_deployments`` — the only remaining
        unscoped search after the legacy path was removed. The ``by_ids``
        filter is the bound on the result set; the parent resolver has
        already authorised access to whatever entity references these IDs,
        and the action is unscoped at the service layer (the admin label
        is enforced at the resolver, not here).

        Output is aligned with the input ``deployment_ids`` order; missing
        IDs come back as ``None``.
        """
        if not deployment_ids:
            return []
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=len(deployment_ids)),
            conditions=[DeploymentConditions.by_ids(deployment_ids)],
        )
        action_result = (
            await self._processors.deployment_admin.admin_search_deployments.wait_for_complete(
                AdminSearchDeploymentsAction(querier=querier)
            )
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
        revision_map: dict[uuid.UUID, RevisionNode] = {
            data.id: self._revision_data_to_dto(data) for data in action_result.data
        }
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

    def _convert_deployment_filter(self, f: DeploymentFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
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
        if f.status is not None:
            if f.status.equals is not None:
                lifecycles = _status_to_lifecycles(ModelDeploymentStatus(f.status.equals))
                if lifecycles:
                    conditions.append(DeploymentConditions.by_status_in(lifecycles))
            if f.status.in_ is not None:
                lifecycles = _statuses_to_lifecycles([
                    ModelDeploymentStatus(s) for s in f.status.in_
                ])
                if lifecycles:
                    conditions.append(DeploymentConditions.by_status_in(lifecycles))
            if f.status.not_equals is not None:
                lifecycles = _status_to_lifecycles(ModelDeploymentStatus(f.status.not_equals))
                if lifecycles:
                    conditions.append(DeploymentConditions.by_status_not_in(lifecycles))
            if f.status.not_in is not None:
                lifecycles = _statuses_to_lifecycles([
                    ModelDeploymentStatus(s) for s in f.status.not_in
                ])
                if lifecycles:
                    conditions.append(DeploymentConditions.by_status_not_in(lifecycles))
        if f.open_to_public is not None:
            conditions.append(DeploymentConditions.by_open_to_public(f.open_to_public))
        if f.tags is not None:
            condition = self.convert_string_filter(
                f.tags,
                contains_factory=DeploymentConditions.by_tag_contains,
                equals_factory=DeploymentConditions.by_tag_equals,
                starts_with_factory=DeploymentConditions.by_tag_starts_with,
                ends_with_factory=DeploymentConditions.by_tag_ends_with,
                in_factory=DeploymentConditions.by_tag_in,
            )
            if condition is not None:
                conditions.append(condition)
        if f.endpoint_url is not None:
            condition = self.convert_string_filter(
                f.endpoint_url,
                contains_factory=DeploymentConditions.by_url_contains,
                equals_factory=DeploymentConditions.by_url_equals,
                starts_with_factory=DeploymentConditions.by_url_starts_with,
                ends_with_factory=DeploymentConditions.by_url_ends_with,
                in_factory=DeploymentConditions.by_url_in,
            )
            if condition is not None:
                conditions.append(condition)
        if f.domain_name is not None:
            condition = self.convert_string_filter(
                f.domain_name,
                contains_factory=DeploymentConditions.by_domain_name_contains,
                equals_factory=DeploymentConditions.by_domain_name_equals,
                starts_with_factory=DeploymentConditions.by_domain_name_starts_with,
                ends_with_factory=DeploymentConditions.by_domain_name_ends_with,
                in_factory=DeploymentConditions.by_domain_name_in,
            )
            if condition is not None:
                conditions.append(condition)
        if f.project_id is not None:
            uuid_condition = self.convert_uuid_filter(
                f.project_id,
                equals_factory=DeploymentConditions.by_project_filter_equals,
                in_factory=DeploymentConditions.by_project_filter_in,
            )
            if uuid_condition is not None:
                conditions.append(uuid_condition)
        if f.resource_group is not None:
            condition = self.convert_string_filter(
                f.resource_group,
                contains_factory=DeploymentConditions.by_resource_group_contains,
                equals_factory=DeploymentConditions.by_resource_group_equals,
                starts_with_factory=DeploymentConditions.by_resource_group_starts_with,
                ends_with_factory=DeploymentConditions.by_resource_group_ends_with,
                in_factory=DeploymentConditions.by_resource_group_in,
            )
            if condition is not None:
                conditions.append(condition)
        if f.created_user_id is not None:
            uuid_condition = self.convert_uuid_filter(
                f.created_user_id,
                equals_factory=DeploymentConditions.by_created_user_filter_equals,
                in_factory=DeploymentConditions.by_created_user_filter_in,
            )
            if uuid_condition is not None:
                conditions.append(uuid_condition)
        if f.created_at is not None:
            dt_condition = f.created_at.build_query_condition(
                before_factory=DeploymentConditions.by_created_at_before,
                after_factory=DeploymentConditions.by_created_at_after,
                equals_factory=DeploymentConditions.by_created_at_equals,
            )
            if dt_condition is not None:
                conditions.append(dt_condition)
        if f.destroyed_at is not None:
            dt_condition = f.destroyed_at.build_query_condition(
                before_factory=DeploymentConditions.by_destroyed_at_before,
                after_factory=DeploymentConditions.by_destroyed_at_after,
                equals_factory=DeploymentConditions.by_destroyed_at_equals,
                is_null_factory=DeploymentConditions.by_destroyed_at_is_null,
                is_not_null_factory=DeploymentConditions.by_destroyed_at_is_not_null,
            )
            if dt_condition is not None:
                conditions.append(dt_condition)
        if f.AND:
            for sub in f.AND:
                conditions.extend(self._convert_deployment_filter(sub))
        if f.OR:
            or_groups: list[QueryCondition] = []
            for sub in f.OR:
                sub_conditions = self._convert_deployment_filter(sub)
                if sub_conditions:
                    or_groups.append(combine_conditions_and(sub_conditions))
            if or_groups:
                conditions.append(combine_conditions_or(or_groups))
        if f.NOT:
            for sub in f.NOT:
                sub_conditions = self._convert_deployment_filter(sub)
                if sub_conditions:
                    conditions.append(negate_conditions(sub_conditions))
        return conditions

    def _build_deployment_querier(self, input: SearchDeploymentsInput) -> BatchQuerier:
        conditions: list[QueryCondition] = []
        if input.filter:
            conditions.extend(self._convert_deployment_filter(input.filter))
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

    def _convert_revision_filter(self, f: RevisionFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if f.revision_number is not None:
            condition = self.convert_int_filter(
                f.revision_number,
                RevisionConditions.by_revision_number,
            )
            if condition is not None:
                conditions.append(condition)
        if f.image_id is not None:
            uuid_condition = self.convert_uuid_filter(
                f.image_id,
                equals_factory=RevisionConditions.by_image_filter_equals,
                in_factory=RevisionConditions.by_image_filter_in,
            )
            if uuid_condition is not None:
                conditions.append(uuid_condition)
        if f.model_vfolder_id is not None:
            uuid_condition = self.convert_uuid_filter(
                f.model_vfolder_id,
                equals_factory=RevisionConditions.by_model_vfolder_filter_equals,
                in_factory=RevisionConditions.by_model_vfolder_filter_in,
            )
            if uuid_condition is not None:
                conditions.append(uuid_condition)
        if f.resource_group is not None:
            condition = self.convert_string_filter(
                f.resource_group,
                contains_factory=RevisionConditions.by_resource_group_contains,
                equals_factory=RevisionConditions.by_resource_group_equals,
                starts_with_factory=RevisionConditions.by_resource_group_starts_with,
                ends_with_factory=RevisionConditions.by_resource_group_ends_with,
                in_factory=RevisionConditions.by_resource_group_in,
            )
            if condition is not None:
                conditions.append(condition)
        if f.cluster_mode is not None:
            condition = self.convert_string_filter(
                f.cluster_mode,
                contains_factory=RevisionConditions.by_cluster_mode_contains,
                equals_factory=RevisionConditions.by_cluster_mode_equals,
                starts_with_factory=RevisionConditions.by_cluster_mode_starts_with,
                ends_with_factory=RevisionConditions.by_cluster_mode_ends_with,
                in_factory=RevisionConditions.by_cluster_mode_in,
            )
            if condition is not None:
                conditions.append(condition)
        if f.created_at is not None:
            dt_condition = f.created_at.build_query_condition(
                before_factory=RevisionConditions.by_created_at_before,
                after_factory=RevisionConditions.by_created_at_after,
                equals_factory=RevisionConditions.by_created_at_equals,
            )
            if dt_condition is not None:
                conditions.append(dt_condition)
        if f.AND:
            for sub in f.AND:
                conditions.extend(self._convert_revision_filter(sub))
        if f.OR:
            or_groups: list[QueryCondition] = []
            for sub in f.OR:
                sub_conditions = self._convert_revision_filter(sub)
                if sub_conditions:
                    or_groups.append(combine_conditions_and(sub_conditions))
            if or_groups:
                conditions.append(combine_conditions_or(or_groups))
        if f.NOT:
            for sub in f.NOT:
                sub_conditions = self._convert_revision_filter(sub)
                if sub_conditions:
                    conditions.append(negate_conditions(sub_conditions))
        return conditions

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
            conditions.extend(self._convert_revision_filter(f))
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

    def _convert_route_filter(self, f: RouteFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
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
        if f.AND:
            for sub in f.AND:
                conditions.extend(self._convert_route_filter(sub))
        if f.OR:
            or_groups: list[QueryCondition] = []
            for sub in f.OR:
                sub_conditions = self._convert_route_filter(sub)
                if sub_conditions:
                    or_groups.append(combine_conditions_and(sub_conditions))
            if or_groups:
                conditions.append(combine_conditions_or(or_groups))
        if f.NOT:
            for sub in f.NOT:
                sub_conditions = self._convert_route_filter(sub)
                if sub_conditions:
                    conditions.append(negate_conditions(sub_conditions))
        return conditions

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
            conditions.extend(self._convert_route_filter(f))
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

    def _convert_access_token_filter(self, f: AccessTokenFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if f.token is not None:
            condition = self.convert_string_filter(
                f.token,
                contains_factory=AccessTokenConditions.by_token_contains,
                equals_factory=AccessTokenConditions.by_token_equals,
                starts_with_factory=AccessTokenConditions.by_token_starts_with,
                ends_with_factory=AccessTokenConditions.by_token_ends_with,
                in_factory=AccessTokenConditions.by_token_in,
            )
            if condition is not None:
                conditions.append(condition)
        if f.expires_at is not None:
            condition = f.expires_at.build_query_condition(
                before_factory=AccessTokenConditions.by_expires_at_before,
                after_factory=AccessTokenConditions.by_expires_at_after,
                equals_factory=AccessTokenConditions.by_expires_at_equals,
            )
            if condition is not None:
                conditions.append(condition)
        if f.created_at is not None:
            condition = f.created_at.build_query_condition(
                before_factory=AccessTokenConditions.by_created_at_before,
                after_factory=AccessTokenConditions.by_created_at_after,
                equals_factory=AccessTokenConditions.by_created_at_equals,
            )
            if condition is not None:
                conditions.append(condition)
        if f.AND:
            for sub in f.AND:
                conditions.extend(self._convert_access_token_filter(sub))
        if f.OR:
            or_groups: list[QueryCondition] = []
            for sub in f.OR:
                sub_conditions = self._convert_access_token_filter(sub)
                if sub_conditions:
                    or_groups.append(combine_conditions_and(sub_conditions))
            if or_groups:
                conditions.append(combine_conditions_or(or_groups))
        if f.NOT:
            for sub in f.NOT:
                sub_conditions = self._convert_access_token_filter(sub)
                if sub_conditions:
                    conditions.append(negate_conditions(sub_conditions))
        return conditions

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
        if input.filter:
            conditions.extend(self._convert_access_token_filter(input.filter))
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

    def _convert_auto_scaling_rule_filter(self, f: AutoScalingRuleFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if f.created_at is not None:
            condition = f.created_at.build_query_condition(
                before_factory=AutoScalingRuleConditions.by_created_at_before,
                after_factory=AutoScalingRuleConditions.by_created_at_after,
                equals_factory=AutoScalingRuleConditions.by_created_at_equals,
            )
            if condition is not None:
                conditions.append(condition)
        if f.last_triggered_at is not None:
            condition = f.last_triggered_at.build_query_condition(
                before_factory=AutoScalingRuleConditions.by_last_triggered_at_before,
                after_factory=AutoScalingRuleConditions.by_last_triggered_at_after,
                equals_factory=AutoScalingRuleConditions.by_last_triggered_at_equals,
                is_null_factory=AutoScalingRuleConditions.by_last_triggered_at_is_null,
                is_not_null_factory=AutoScalingRuleConditions.by_last_triggered_at_is_not_null,
            )
            if condition is not None:
                conditions.append(condition)
        if f.AND:
            for sub in f.AND:
                conditions.extend(self._convert_auto_scaling_rule_filter(sub))
        if f.OR:
            or_groups: list[QueryCondition] = []
            for sub in f.OR:
                sub_conditions = self._convert_auto_scaling_rule_filter(sub)
                if sub_conditions:
                    or_groups.append(combine_conditions_and(sub_conditions))
            if or_groups:
                conditions.append(combine_conditions_or(or_groups))
        if f.NOT:
            for sub in f.NOT:
                sub_conditions = self._convert_auto_scaling_rule_filter(sub)
                if sub_conditions:
                    conditions.append(negate_conditions(sub_conditions))
        return conditions

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
        if input.filter:
            conditions.extend(self._convert_auto_scaling_rule_filter(input.filter))
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

    def _convert_replica_filter(self, f: ReplicaFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
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
            if st.not_equals is not None:
                conditions.append(
                    RouteConditions.by_status_not_equals(ManagerRouteStatus(st.not_equals.value))
                )
            if st.not_in is not None:
                conditions.append(
                    RouteConditions.by_status_not_in([
                        ManagerRouteStatus(s.value) for s in st.not_in
                    ])
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
            if ts.not_equals is not None:
                conditions.append(
                    RouteConditions.by_traffic_status_not_equals(
                        ManagerRouteTrafficStatus(ts.not_equals.value)
                    )
                )
            if ts.not_in is not None:
                conditions.append(
                    RouteConditions.by_traffic_status_not_in([
                        ManagerRouteTrafficStatus(s.value) for s in ts.not_in
                    ])
                )
        if f.AND:
            for sub in f.AND:
                conditions.extend(self._convert_replica_filter(sub))
        if f.OR:
            or_groups: list[QueryCondition] = []
            for sub in f.OR:
                sub_conditions = self._convert_replica_filter(sub)
                if sub_conditions:
                    or_groups.append(combine_conditions_and(sub_conditions))
            if or_groups:
                conditions.append(combine_conditions_or(or_groups))
        if f.NOT:
            for sub in f.NOT:
                sub_conditions = self._convert_replica_filter(sub)
                if sub_conditions:
                    conditions.append(negate_conditions(sub_conditions))
        return conditions

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
            conditions.extend(self._convert_replica_filter(f))
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
        revision_id: DeploymentRevisionID,
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
            or_groups: list[QueryCondition] = []
            for sub in filter_.OR:
                sub_conditions = self._convert_allocated_slot_filter(sub, conditions_cls)
                if sub_conditions:
                    or_groups.append(combine_conditions_and(sub_conditions))
            if or_groups:
                conditions.append(combine_conditions_or(or_groups))
        if filter_.NOT:
            for sub in filter_.NOT:
                sub_conditions = self._convert_allocated_slot_filter(sub, conditions_cls)
                if sub_conditions:
                    conditions.append(negate_conditions(sub_conditions))
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
                case DeploymentOrderField.DESTROYED_AT:
                    result.append(DeploymentOrders.destroyed_at(ascending))
                case DeploymentOrderField.DOMAIN:
                    result.append(DeploymentOrders.domain(ascending))
                case DeploymentOrderField.PROJECT:
                    result.append(DeploymentOrders.project(ascending))
                case DeploymentOrderField.RESOURCE_GROUP:
                    result.append(DeploymentOrders.resource_group(ascending))
                case DeploymentOrderField.TAG:
                    result.append(DeploymentOrders.tag(ascending))
        return result

    @staticmethod
    def _convert_revision_orders(orders: list[RevisionOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for o in orders:
            ascending = o.direction == OrderDirection.ASC
            match o.field:
                case RevisionOrderField.REVISION_NUMBER:
                    result.append(RevisionOrders.revision_number(ascending))
                case RevisionOrderField.CREATED_AT:
                    result.append(RevisionOrders.created_at(ascending))
                case RevisionOrderField.RESOURCE_GROUP:
                    result.append(RevisionOrders.resource_group(ascending))
                case RevisionOrderField.CLUSTER_MODE:
                    result.append(RevisionOrders.cluster_mode(ascending))
                case RevisionOrderField.RUNTIME_VARIANT_NAME:
                    result.append(RevisionOrders.runtime_variant_name(ascending))
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
                resource_group_name=data.metadata.resource_group_name,
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
            options=deployment_options_to_info(data.options),
            scaling_state=data.scaling_state,
            current_revision_id=data.current_revision_id,
            deploying_revision_id=data.deploying_revision_id,
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
                subpath=data.model_mount_config.subpath,
            )
        return RevisionNode(
            id=data.id,
            deployment_id=data.deployment_id,
            revision_number=data.revision_number,
            image_id=data.image_id,
            cluster_config=ClusterConfigInfoDTO(
                mode=data.cluster_config.mode.name,
                size=data.cluster_config.size,
            ),
            resource_config=ResourceConfigInfoDTO(
                resource_group_name=data.resource_config.resource_group_name,
                resource_slots=ResourceSlotInfo(
                    entries=[
                        ResourceSlotEntryInfo(resource_type=str(k), quantity=Decimal(str(v)))
                        for k, v in data.resource_config.resource_slot.items()
                    ],
                ),
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
                runtime_variant_id=data.model_runtime_config.runtime_variant_id,
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
                    mount_perm=m.mount_perm,
                    subpath=m.subpath,
                )
                for m in data.model_mount_config.extra_mounts
            ],
            revision_preset_id=data.preset.preset_id,
        )

    @staticmethod
    def _route_info_to_dto(data: RouteInfo) -> RouteNode:
        return RouteNode(
            id=data.route_id,
            deployment_id=data.deployment_id,
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
            status=_to_common_route_status(data.status),
            traffic_status=_to_common_route_traffic_status(data.traffic_status),
            health_status=_to_common_route_health_status(data.health_status),
            created_at=data.created_at,
        )
