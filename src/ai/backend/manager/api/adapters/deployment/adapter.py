"""Deployment adapter bridging DTOs and Processors."""

from __future__ import annotations

import uuid
from collections.abc import Collection, Mapping, Sequence
from dataclasses import replace
from decimal import Decimal
from functools import lru_cache
from typing import TYPE_CHECKING, assert_never
from uuid import UUID

from ai.backend.manager.models.resource_slot.row import DeploymentRevisionResourceSlotRow

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.deployment.coordinator import DeploymentCoordinator

from ai.backend.common.config import (
    ModelConfig,
    ModelDefinition,
    ModelServiceConfig,
)
from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.entity.auto_scaling_rule import AutoScalingRuleID
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionID
from ai.backend.common.data.entity.deployment_token import DeploymentTokenID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.replica import ReplicaID
from ai.backend.common.data.entity.replica_group import ReplicaGroupID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.runtime_variant_preset import RuntimeVariantPresetID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.filter_specs import UUIDEqualMatchSpec
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
    AccessTokenOrder,
    ActivateRevisionInput,
    AddRevisionInput,
    AddRevisionOptions,
    AdminSearchDeploymentsInput,
    AdminSearchRevisionsInput,
    AutoScalingRuleFilter,
    AutoScalingRuleOrder,
    BulkDeleteAccessTokensInput,
    CreateAccessTokenInput,
    CreateDeploymentInput,
    DeleteAccessTokenInput,
    DeleteDeploymentInput,
    DeploymentFilter,
    DeploymentOrder,
    DeploymentStatusFilter,
    ReplaceDeploymentOptionsInput,
    ReplicaFilter,
    ReplicaOrder,
    RevisionFilter,
    RevisionOrder,
    RouteFilter,
    RouteOrder,
    ScopedSearchDeploymentsInput,
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
    AdminRefreshDeploymentRevisionsPayload,
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
    ReplaceDeploymentOptionsPayload,
    ReplicaNode,
    RevisionNode,
    RevisionRefreshResultInfo,
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
    AccessTokenOrderField,
    AutoScalingRuleOrderField,
    BlueGreenConfigInfo,
    BlueGreenStrategySpecInfo,
    ClusterConfigInfoDTO,
    DeploymentMetadataInfoDTO,
    DeploymentNetworkAccessInfoDTO,
    DeploymentOrderField,
    DeploymentPolicyInfo,
    DeploymentScope,
    DeploymentStrategyInfoDTO,
    DeploymentUsedBy,
    EnvironmentVariableEntryInfoDTO,
    EnvironmentVariablesInfoDTO,
    ExtraVFolderMountGQLDTO,
    ModelConfigInfoDTO,
    ModelDefinitionInfoDTO,
    ModelHealthCheckInfoDTO,
    ModelMetadataInfoDTO,
    ModelMountConfigInfoDTO,
    ModelRuntimeConfigInfoDTO,
    ModelServiceConfigInfoDTO,
    OrderDirection,
    PreStartActionInfoDTO,
    ReplicaOrderField,
    ReplicaStateInfo,
    ResourceConfigInfoDTO,
    RevisionOrderField,
    RollingUpdateConfigInfo,
    RollingUpdateStrategySpecInfo,
    RouteOrderField,
    RuntimeVariantPresetValueInfoDTO,
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
from ai.backend.common.model_service_start_command_compat import to_legacy_start_command
from ai.backend.common.schema.deployment import BlueGreenSpec, RollingUpdateSpec
from ai.backend.common.tristate.unset import Unset
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
    AccessTokenOperationScope,
    AutoScalingRuleOperationScope,
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
    ReplicaGroupData,
    ReplicaOperationScope,
    ReplicaSpec,
    ResourceSpec,
    RevisionOperationScope,
    RouteInfo,
    RouteOperationScope,
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
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetValueData
from ai.backend.manager.errors.base.field import FieldNotFoundError
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.errors.deployment import DeploymentRevisionNotFound
from ai.backend.manager.errors.service import EndpointTokenNotFound
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import (
    combine_conditions_and,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.models.deployment_policy.row import DeploymentPolicyRow
from ai.backend.manager.models.deployment_policy.searchable_fields import (
    DeploymentPolicySearchableFields,
)
from ai.backend.manager.models.deployment_policy.searchers import DeploymentPolicySearcher
from ai.backend.manager.models.deployment_policy.upserters import DeploymentPolicyUpserter
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision.searchable_fields import (
    ModelRevisionSearchableFields,
)
from ai.backend.manager.models.deployment_revision.searchers import ModelRevisionSearcher
from ai.backend.manager.models.endpoint import (
    EndpointAutoScalingRuleRow,
    EndpointRow,
    EndpointTokenRow,
)
from ai.backend.manager.models.endpoint.scopes import (
    DeploymentTarget,
    DomainDeploymentTarget,
    ProjectDeploymentTarget,
    UserDeploymentTarget,
)
from ai.backend.manager.models.endpoint.searchable_fields import (
    AutoScalingRuleSearchableFields,
    DeploymentAccessTokenSearchableFields,
    DeploymentSearchableFields,
)
from ai.backend.manager.models.endpoint.searchers import (
    AutoScalingRuleSearcher,
    DeploymentAccessTokenSearcher,
    DeploymentSearcher,
)
from ai.backend.manager.models.endpoint.updaters import DeploymentUpdater
from ai.backend.manager.models.resource_slot.conditions import RevisionResourceSlotConditions
from ai.backend.manager.models.resource_slot.orders import (
    ALLOCATED_SLOT_DEFAULT_FORWARD_ORDER,
    resolve_allocated_slot_revision_order,
)
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.routing.searchable_fields import ReplicaSearchableFields
from ai.backend.manager.models.routing.searchers import ModelReplicaSearcher, RouteInfoSearcher
from ai.backend.manager.models.specs.search.usage import UsedBy
from ai.backend.manager.models.specs.searcher import GlobalSearcher, ScopedSearcher
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.deployment.actions.access_token.bulk_delete_access_tokens import (
    BulkDeleteAccessTokensAction,
)
from ai.backend.manager.services.deployment.actions.access_token.bulk_get_access_tokens import (
    BulkGetAccessTokensAction,
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
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.bulk_get_auto_scaling_rules import (
    BulkGetAutoScalingRulesAction,
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
from ai.backend.manager.services.deployment.actions.bulk_get import BulkGetDeploymentsAction
from ai.backend.manager.services.deployment.actions.create_deployment import CreateDeploymentAction
from ai.backend.manager.services.deployment.actions.deployment_policy.bulk_get_deployment_policies import (
    BulkGetDeploymentPoliciesAction,
)
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
from ai.backend.manager.services.deployment.actions.global_search_replicas import (
    GlobalSearchReplicasAction,
)
from ai.backend.manager.services.deployment.actions.lookup_owner import (
    LookupAutoScalingRuleDeploymentAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.add_model_revision import (
    AddModelRevisionAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.bulk_get_revisions import (
    BulkGetRevisionsAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.get_revision_by_id import (
    GetRevisionByIdAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.global_search_revisions import (
    GlobalSearchRevisionsAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.search_revision_resource_slots import (
    SearchRevisionResourceSlotsAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.search_revisions import (
    SearchRevisionsAction,
)
from ai.backend.manager.services.deployment.actions.refresh_deployment_revisions import (
    GlobalRefreshDeploymentRevisionsAction,
)
from ai.backend.manager.services.deployment.actions.replace_deployment_options import (
    ReplaceDeploymentOptionsAction,
)
from ai.backend.manager.services.deployment.actions.replica.bulk_get_replicas import (
    BulkGetReplicasAction,
)
from ai.backend.manager.services.deployment.actions.replica_group.bulk_get_replica_groups import (
    BulkGetReplicaGroupsAction,
)
from ai.backend.manager.services.deployment.actions.revision_operations import (
    ActivateRevisionAction,
)
from ai.backend.manager.services.deployment.actions.route.bulk_get_routes import (
    BulkGetRoutesAction,
)
from ai.backend.manager.services.deployment.actions.route.search_routes import SearchRoutesAction
from ai.backend.manager.services.deployment.actions.route.update_route_traffic_status import (
    UpdateRouteTrafficStatusAction,
)
from ai.backend.manager.services.deployment.actions.scoped_search import (
    ScopedSearchDeploymentsAction,
)
from ai.backend.manager.services.deployment.actions.search_deployments import (
    GlobalSearchDeploymentsAction,
)
from ai.backend.manager.services.deployment.actions.search_replicas import SearchReplicasAction
from ai.backend.manager.services.deployment.actions.sync_replicas import SyncReplicaAction
from ai.backend.manager.services.deployment.actions.update_deployment import UpdateDeploymentAction
from ai.backend.manager.services.deployment.processors import DeploymentProcessors
from ai.backend.manager.types import OptionalState, TriState

DEFAULT_PAGINATION_LIMIT = 10


def _model_service_config_to_dto(service: ModelServiceConfig) -> ModelServiceConfigInfoDTO:
    health_check = None
    if service.health_check is not None:
        health_check = ModelHealthCheckInfoDTO(
            enable=service.health_check.enable,
            interval=service.health_check.interval,
            path=service.health_check.path,
            max_retries=service.health_check.max_retries,
            max_wait_time=service.health_check.max_wait_time,
            expected_status_code=service.health_check.expected_status_code,
            initial_delay=service.health_check.initial_delay,
        )
    return ModelServiceConfigInfoDTO(
        pre_start_actions=[
            PreStartActionInfoDTO(action=a.action, args=a.args) for a in service.pre_start_actions
        ],
        command=service.start_command,
        start_command=to_legacy_start_command(service.start_command),
        shell=service.shell,
        port=service.port,
        health_check=health_check,
    )


def _model_config_to_dto(config: ModelConfig) -> ModelConfigInfoDTO:
    metadata = None
    if config.metadata is not None:
        metadata = ModelMetadataInfoDTO(
            author=config.metadata.author,
            title=config.metadata.title,
            version=config.metadata.version,
            created=config.metadata.created,
            last_modified=config.metadata.last_modified,
            description=config.metadata.description,
            task=config.metadata.task,
            category=config.metadata.category,
            architecture=config.metadata.architecture,
            framework=config.metadata.framework,
            label=config.metadata.label,
            license=config.metadata.license,
            min_resource=config.metadata.min_resource,
        )
    return ModelConfigInfoDTO(
        name=config.name,
        model_path=config.model_path,
        service=(
            _model_service_config_to_dto(config.service) if config.service is not None else None
        ),
        metadata=metadata,
    )


def _model_definition_to_dto(
    definition: ModelDefinition | None,
) -> ModelDefinitionInfoDTO | None:
    if definition is None:
        return None
    return ModelDefinitionInfoDTO(
        models=[_model_config_to_dto(m) for m in definition.models],
    )


@lru_cache(maxsize=1)
def _get_deployment_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=DeploymentSearchableFields.own.created_at.order.apply(ascending=False),
        cursor_column=EndpointRow.id,
    )


def _get_deployment_policy_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=DeploymentPolicyRow.created_at.desc(),
        cursor_column=DeploymentPolicyRow.id,
    )


@lru_cache(maxsize=1)
def _get_revision_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=ModelRevisionSearchableFields.own.created_at.order.apply(ascending=False),
        cursor_column=DeploymentRevisionRow.id,
    )


@lru_cache(maxsize=1)
def _get_route_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=ReplicaSearchableFields.own.created_at.order.apply(ascending=False),
        cursor_column=RoutingRow.id,
    )


@lru_cache(maxsize=1)
def _get_access_token_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=DeploymentAccessTokenSearchableFields.own.created_at.order.apply(
            ascending=False
        ),
        cursor_column=EndpointTokenRow.id,
    )


@lru_cache(maxsize=1)
def _get_auto_scaling_rule_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=AutoScalingRuleSearchableFields.own.created_at.order.apply(ascending=False),
        cursor_column=EndpointAutoScalingRuleRow.id,
    )


@lru_cache(maxsize=1)
def _get_replica_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=ReplicaSearchableFields.own.created_at.order.apply(ascending=False),
        cursor_column=RoutingRow.id,
    )


@lru_cache(maxsize=1)
def _get_revision_resource_slot_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=ALLOCATED_SLOT_DEFAULT_FORWARD_ORDER,
        cursor_column=DeploymentRevisionResourceSlotRow.id,
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

    _deployment: DeploymentProcessors
    _deployment_coordinator: DeploymentCoordinator

    def __init__(
        self,
        deployment: DeploymentProcessors,
        deployment_coordinator: DeploymentCoordinator,
    ) -> None:
        self._deployment = deployment
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
                model_mount_perm=initial_revision.model_mount_config.mount_perm,
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
                runtime_variant_preset_values=[
                    RuntimeVariantPresetValueData(
                        preset_id=RuntimeVariantPresetID(preset_input.preset_id),
                        value=preset_input.value,
                    )
                    for preset_input in (
                        initial_revision.model_runtime_config.runtime_variant_preset_values or []
                    )
                ],
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
        action_result = await self._deployment.create_deployment.run(
            CreateDeploymentAction(
                project_id=ProjectID(creator.metadata.project),
                creator=creator,
                auto_activate=initial_revision.auto_activate
                if initial_revision is not None
                else False,
            )
        )
        return CreateDeploymentPayload(deployment=self._deployment_data_to_dto(action_result.data))

    async def admin_search(
        self,
        input: AdminSearchDeploymentsInput,
    ) -> AdminSearchDeploymentsPayload:
        """Search deployments (admin, no scope)."""
        action_result = await self._deployment.global_search.run(
            GlobalSearchDeploymentsAction(
                searcher=GlobalSearcher(
                    used_by=self._used_by(input.used_by),
                    searcher=self._build_deployment_searcher(input),
                )
            )
        )
        return AdminSearchDeploymentsPayload(
            items=[self._deployment_data_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _used_by(self, used_by: DeploymentUsedBy | None) -> list[UsedBy]:
        """The uses the request named."""
        if used_by is None:
            return []
        linked = DeploymentSearchableFields.linked
        return [
            linked.resource_groups.used_by(ResourceGroupID(entity_id))
            for entity_id in used_by.resource_group or ()
        ]

    def _scope_targets(self, scope: DeploymentScope) -> list[DeploymentTarget]:
        """The scope targets the request named, in the order the input lists them."""
        targets: list[DeploymentTarget] = [
            DomainDeploymentTarget(domain_id=DomainID(entry.value)) for entry in scope.domain or ()
        ]
        targets.extend(
            ProjectDeploymentTarget(project_id=ProjectID(entry.value))
            for entry in scope.project or ()
        )
        targets.extend(
            UserDeploymentTarget(user_id=UserID(entry.value)) for entry in scope.user or ()
        )
        return targets

    async def scoped_search(
        self,
        input: ScopedSearchDeploymentsInput,
    ) -> AdminSearchDeploymentsPayload:
        """Search the deployments the named scopes reach, combined with OR."""
        action_result = await self._deployment.scoped_search.run(
            ScopedSearchDeploymentsAction(
                searcher=ScopedSearcher(
                    scopes=self._scope_targets(input.scope),
                    used_by=self._used_by(input.used_by),
                    searcher=self._build_scoped_deployment_searcher(input),
                )
            )
        )
        return AdminSearchDeploymentsPayload(
            items=[self._deployment_data_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def my_search(
        self,
        input: AdminSearchDeploymentsInput,
    ) -> AdminSearchDeploymentsPayload:
        """Search deployments created by the current user."""
        user = current_user()
        if user is None:
            raise RuntimeError("No authenticated user in context")
        action_result = await self._deployment.scoped_search.run(
            ScopedSearchDeploymentsAction(
                searcher=ScopedSearcher(
                    scopes=[UserDeploymentTarget(user_id=UserID(user.user_id))],
                    used_by=self._used_by(input.used_by),
                    searcher=self._build_deployment_searcher(input),
                )
            )
        )
        return AdminSearchDeploymentsPayload(
            items=[self._deployment_data_to_dto(item) for item in action_result.items],
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
        action_result = await self._deployment.scoped_search.run(
            ScopedSearchDeploymentsAction(
                searcher=ScopedSearcher(
                    scopes=[ProjectDeploymentTarget(project_id=ProjectID(project_id))],
                    used_by=self._used_by(input.used_by),
                    searcher=self._build_deployment_searcher(input),
                )
            )
        )
        return AdminSearchDeploymentsPayload(
            items=[self._deployment_data_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def get(self, deployment_id: DeploymentID) -> DeploymentNode:
        """Retrieve a single deployment by ID."""
        action_result = await self._deployment.get_deployment_by_id.run(
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
        updater = DeploymentUpdater(
            deployment_id=deployment_id,
            name=OptionalState.from_unset(input.name),
            tag=self._convert_tag_state(input.tags),
            replica_count=OptionalState.from_unset(input.replica_count),
            open_to_public=OptionalState.from_unset(input.open_to_public),
        )
        action_result = await self._deployment.update_deployment.run(
            UpdateDeploymentAction(deployment_id=deployment_id, updater=updater)
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
        action_result = await self._deployment.replace_deployment_options.run(
            ReplaceDeploymentOptionsAction(
                deployment_id=deployment_id,
                options=options,
            )
        )
        return ReplaceDeploymentOptionsPayload(
            deployment_id=deployment_id,
            options=deployment_options_to_info(action_result.options),
        )

    async def sync_replicas(self, input: SyncReplicaInput) -> SyncReplicaPayload:
        """Force sync replica information for a deployment."""
        await self._deployment.sync_replicas.run(
            SyncReplicaAction(deployment_id=DeploymentID(input.model_deployment_id))
        )
        return SyncReplicaPayload(success=True)

    async def activate_revision(self, input: ActivateRevisionInput) -> ActivateRevisionPayload:
        """Activate a specific revision as the current revision."""
        action_result = await self._deployment.activate_revision.run(
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
        action_result = await self._deployment.global_refresh_revisions.run(
            GlobalRefreshDeploymentRevisionsAction()
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
        await self._deployment.destroy_deployment.run(
            DestroyDeploymentAction(deployment_id=DeploymentID(input.id))
        )
        return DeleteDeploymentPayload(id=input.id)

    # ------------------------------------------------------------------
    # Access token operations
    # ------------------------------------------------------------------

    async def _auto_scaling_rule_deployment(self, rule_id: UUID) -> DeploymentID:
        result = await self._deployment.lookup_auto_scaling_rule_deployment.run(
            LookupAutoScalingRuleDeploymentAction(rule_id=rule_id)
        )
        return DeploymentID(result.entity_id())

    async def create_access_token(
        self,
        input: CreateAccessTokenInput,
    ) -> CreateAccessTokenPayload:
        """Create a new access token for a deployment."""
        creator = ModelDeploymentAccessTokenCreator(
            model_deployment_id=DeploymentID(input.model_deployment_id),
            expires_at=input.expires_at,
        )
        action_result = await self._deployment.create_access_token.run(
            CreateAccessTokenAction(
                deployment_id=DeploymentID(input.model_deployment_id), creator=creator
            )
        )
        return CreateAccessTokenPayload(
            access_token=self._access_token_data_to_dto(action_result.data)
        )

    async def get_access_token(
        self,
        token_id: UUID,
    ) -> GetAccessTokenPayload:
        """Get a single access token by ID."""
        action_result = await self._deployment.get_access_token.run(
            GetAccessTokenAction(access_token_id=DeploymentTokenID(token_id))
        )
        return GetAccessTokenPayload(
            access_token=self._access_token_data_to_dto(action_result.data)
        )

    async def delete_access_token(
        self,
        input: DeleteAccessTokenInput,
    ) -> DeleteAccessTokenPayload:
        """Delete an access token."""
        action_result = await self._deployment.delete_access_token.run(
            DeleteAccessTokenAction(access_token_id=DeploymentTokenID(input.id))
        )
        if not action_result.success:
            raise EndpointTokenNotFound(f"Access token {input.id} not found")
        return DeleteAccessTokenPayload(id=input.id)

    async def bulk_delete_access_tokens(
        self,
        input: BulkDeleteAccessTokensInput,
    ) -> BulkDeleteAccessTokensPayload:
        """Bulk delete access tokens; a token missing or refused is left out of the answer."""
        if not input.ids:
            return BulkDeleteAccessTokensPayload(ids=[])
        try:
            action_result = await self._deployment.bulk_delete_access_tokens.run(
                BulkDeleteAccessTokensAction(
                    access_token_ids=[DeploymentTokenID(token_id) for token_id in input.ids]
                )
            )
        except FieldNotFoundError:
            return BulkDeleteAccessTokensPayload(ids=[])
        return BulkDeleteAccessTokensPayload(
            ids=[token.id for token in action_result.successes.values()]
        )

    async def search_access_tokens(
        self,
        scope: AccessTokenOperationScope,
        input: SearchAccessTokensInput,
    ) -> SearchAccessTokensPayload:
        """Search access tokens scoped to a specific deployment."""
        searcher = self._build_access_token_searcher(input)
        action_result = await self._deployment.search_access_tokens.run(
            SearchAccessTokensAction(
                deployment_ids=[DeploymentID(scope.deployment_id)], searcher=searcher
            )
        )
        return SearchAccessTokensPayload(
            items=[self._access_token_data_to_dto(item) for item in action_result.items],
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
        action_result = await self._deployment.create_auto_scaling_rule.run(
            CreateAutoScalingRuleAction(
                deployment_id=DeploymentID(input.model_deployment_id), creator=creator
            )
        )
        return CreateAutoScalingRulePayload(
            rule=self._auto_scaling_rule_data_to_dto(action_result.data)
        )

    async def search_rules(
        self,
        scope: AutoScalingRuleOperationScope,
        input: SearchAutoScalingRulesInput,
    ) -> SearchAutoScalingRulesPayload:
        """Search auto-scaling rules scoped to a specific deployment."""
        querier = self._build_auto_scaling_rule_querier(input, scope=scope)
        action_result = await self._deployment.search_auto_scaling_rules.run(
            SearchAutoScalingRulesAction(
                searcher=GlobalSearcher(
                    used_by=(),
                    searcher=AutoScalingRuleSearcher(
                        pagination=querier.pagination,
                        conditions=querier.conditions,
                        orders=querier.orders,
                    ),
                )
            )
        )
        return SearchAutoScalingRulesPayload(
            items=[self._auto_scaling_rule_data_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def get_rule(self, rule_id: UUID) -> GetAutoScalingRulePayload:
        """Retrieve a single auto-scaling rule by ID."""
        action_result = await self._deployment.get_auto_scaling_rule.run(
            GetAutoScalingRuleAction(
                deployment_id=await self._auto_scaling_rule_deployment(rule_id),
                auto_scaling_rule_id=rule_id,
            )
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
            metric_source=OptionalState.from_unset(input.metric_source),
            metric_name=OptionalState.from_unset(input.metric_name),
            min_threshold=TriState.from_unset(input.min_threshold),
            max_threshold=TriState.from_unset(input.max_threshold),
            step_size=OptionalState.from_unset(input.step_size),
            time_window=OptionalState.from_unset(input.time_window),
            min_replicas=TriState.from_unset(input.min_replicas),
            max_replicas=TriState.from_unset(input.max_replicas),
            prometheus_query_preset_id=TriState.from_unset(input.prometheus_query_preset_id),
        )
        action_result = await self._deployment.update_auto_scaling_rule.run(
            UpdateAutoScalingRuleAction(
                deployment_id=await self._auto_scaling_rule_deployment(input.id),
                auto_scaling_rule_id=input.id,
                modifier=modifier,
            )
        )
        return UpdateAutoScalingRulePayload(
            rule=self._auto_scaling_rule_data_to_dto(action_result.data)
        )

    async def delete_rule(self, input: DeleteAutoScalingRuleInput) -> DeleteAutoScalingRulePayload:
        """Delete an auto-scaling rule."""
        await self._deployment.delete_auto_scaling_rule.run(
            DeleteAutoScalingRuleAction(
                deployment_id=await self._auto_scaling_rule_deployment(input.id),
                auto_scaling_rule_id=input.id,
            )
        )
        return DeleteAutoScalingRulePayload(id=input.id)

    async def bulk_delete_rules(
        self, input: BulkDeleteAutoScalingRulesInput
    ) -> BulkDeleteAutoScalingRulesPayload:
        """Bulk delete auto-scaling rules; a rule missing or refused is left out of the answer."""
        rule_deployments: dict[UUID, DeploymentID] = {}
        for rule_id in input.ids:
            try:
                rule_deployments[rule_id] = await self._auto_scaling_rule_deployment(rule_id)
            except (GenericBadRequest, FieldNotFoundError):
                continue
        if not rule_deployments:
            return BulkDeleteAutoScalingRulesPayload(ids=[])
        action_result = await self._deployment.bulk_delete_auto_scaling_rules.run(
            BulkDeleteAutoScalingRulesAction(rule_deployments=rule_deployments)
        )
        return BulkDeleteAutoScalingRulesPayload(
            ids=[rule_id for rule_ids in action_result.values().values() for rule_id in rule_ids]
        )

    # ------------------------------------------------------------------
    # Deployment policy operations
    # ------------------------------------------------------------------

    async def get_policy(self, deployment_id: DeploymentID) -> GetDeploymentPolicyPayload:
        """Retrieve a deployment policy by deployment ID."""
        action_result = await self._deployment.get_deployment_policy.run(
            GetDeploymentPolicyAction(deployment_id=deployment_id)
        )
        return GetDeploymentPolicyPayload(policy=self._policy_data_to_dto(action_result.data))

    async def search_policies(
        self,
        input: SearchDeploymentPoliciesInput,
    ) -> SearchDeploymentPoliciesPayload:
        """Search deployment policies with filters and pagination."""
        querier = self._build_policy_querier(input)
        action_result = await self._deployment.search_deployment_policies.run(
            SearchDeploymentPoliciesAction(
                searcher=GlobalSearcher(
                    used_by=(),
                    searcher=DeploymentPolicySearcher(
                        pagination=querier.pagination,
                        conditions=querier.conditions,
                        orders=querier.orders,
                    ),
                )
            )
        )
        return SearchDeploymentPoliciesPayload(
            items=[self._policy_data_to_dto(item) for item in action_result.items],
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
        action_result = await self._deployment.upsert_deployment_policy.run(
            UpsertDeploymentPolicyAction(
                deployment_id=DeploymentID(input.deployment_id),
                upserter=DeploymentPolicyUpserter(
                    strategy=input.strategy,
                    strategy_spec=strategy_spec,
                ),
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
            model_mount_perm=input.model_mount_config.mount_perm,
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

        runtime_variant_preset_values = (
            [
                RuntimeVariantPresetValueData(
                    preset_id=RuntimeVariantPresetID(preset_value_input.preset_id),
                    value=preset_value_input.value,
                )
                for preset_value_input in (
                    input.model_runtime_config.runtime_variant_preset_values or []
                )
            ]
            if input.model_runtime_config is not None
            else []
        )
        adder = ModelRevisionCreator(
            image_id=image_id,
            resource_spec=resource_spec,
            mounts=mounts_creator,
            execution=execution,
            model_definition=model_definition,
            revision_preset_id=input.revision_preset_id,
            runtime_variant_preset_values=runtime_variant_preset_values,
        )
        action_result = await self._deployment.add_model_revision.run(
            AddModelRevisionAction(
                deployment_id=DeploymentID(input.deployment_id),
                adder=adder,
                auto_activate=options.auto_activate,
            )
        )
        return AddRevisionPayload(revision=self._revision_data_to_dto(action_result.revision))

    async def get_revision(self, revision_id: DeploymentRevisionID) -> RevisionNode:
        """Retrieve a single revision by ID."""
        action_result = await self._deployment.get_revision_by_id.run(
            GetRevisionByIdAction(revision_id=revision_id)
        )
        return self._revision_data_to_dto(action_result.data)

    async def search_revisions(
        self,
        scope: RevisionOperationScope,
        input: AdminSearchRevisionsInput,
    ) -> AdminSearchRevisionsPayload:
        """Search model revisions scoped to a specific deployment."""
        searcher = self._build_revision_searcher(input)
        action_result = await self._deployment.search_revisions.run(
            SearchRevisionsAction(
                deployment_ids=[DeploymentID(scope.deployment_id)], searcher=searcher
            )
        )
        return AdminSearchRevisionsPayload(
            items=[self._revision_data_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def admin_search_revisions(
        self,
        input: AdminSearchRevisionsInput,
    ) -> AdminSearchRevisionsPayload:
        """Search model revisions without scope (admin, all deployments)."""
        searcher = self._build_revision_searcher(input)
        action_result = await self._deployment.global_search_revisions.run(
            GlobalSearchRevisionsAction(searcher=GlobalSearcher(used_by=(), searcher=searcher))
        )
        return AdminSearchRevisionsPayload(
            items=[self._revision_data_to_dto(item) for item in action_result.items],
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
        action_result = await self._deployment.search_revision_resource_slots.run(
            SearchRevisionResourceSlotsAction(
                revision_id=revision_id,
                querier=querier,
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
        scope: RouteOperationScope,
        input: SearchRoutesInput,
    ) -> SearchRoutesPayload:
        """Search routes scoped to a specific deployment."""
        querier = self._build_route_querier(input, scope=scope)
        action_result = await self._deployment.search_routes.run(
            SearchRoutesAction(
                searcher=GlobalSearcher(
                    used_by=(),
                    searcher=RouteInfoSearcher(
                        pagination=querier.pagination,
                        conditions=querier.conditions,
                        orders=querier.orders,
                    ),
                )
            )
        )
        return SearchRoutesPayload(
            items=[self._route_info_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    # ------------------------------------------------------------------
    # Replica operations
    # ------------------------------------------------------------------

    async def search_replicas(
        self,
        scope: ReplicaOperationScope,
        input: SearchReplicasInput,
    ) -> SearchReplicasPayload:
        """Search replicas scoped to a specific deployment."""
        searcher = self._build_replica_searcher(input)
        action_result = await self._deployment.search_replicas.run(
            SearchReplicasAction(
                deployment_ids=[DeploymentID(scope.deployment_id)], searcher=searcher
            )
        )
        return SearchReplicasPayload(
            items=[self._replica_data_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def admin_search_replicas(
        self,
        input: SearchReplicasInput,
    ) -> SearchReplicasPayload:
        """Search replicas without scope (admin, all deployments)."""
        searcher = self._build_replica_searcher(input)
        action_result = await self._deployment.global_search_replicas.run(
            GlobalSearchReplicasAction(searcher=GlobalSearcher(used_by=(), searcher=searcher))
        )
        return SearchReplicasPayload(
            items=[self._replica_data_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def get_replica(self, replica_id: UUID) -> ReplicaNode | None:
        """Retrieve a single replica by ID."""
        action_result = await self._deployment.get_replica_by_id.run(
            GetReplicaByIdAction(replica_id=ReplicaID(replica_id))
        )
        return self._replica_data_to_dto(action_result.data)

    async def update_route_traffic(
        self,
        route_id: UUID,
        traffic_status: RouteTrafficStatus,
    ) -> RouteNode:
        """Update the traffic status of a route."""
        action_result = await self._deployment.update_route_traffic_status.run(
            UpdateRouteTrafficStatusAction(
                route_id=ReplicaID(route_id),
                traffic_status=ManagerRouteTrafficStatus(traffic_status.value),
            )
        )
        return self._route_info_to_dto(action_result.route)

    # ------------------------------------------------------------------
    # Batch load methods for DataLoader use
    # ------------------------------------------------------------------

    async def batch_load_by_ids(
        self,
        deployment_ids: Sequence[DeploymentID],
    ) -> list[DeploymentNode | Exception | None]:
        """Batch load deployments by ID for DataLoader use, checked per deployment.

        The current revision is read off each readable deployment's primary replica group.
        """
        if not deployment_ids:
            return []
        result = await self._deployment.bulk_get.run(
            BulkGetDeploymentsAction(ids=list(deployment_ids))
        )
        group_ids = list(
            dict.fromkeys(
                item.value.primary_replica_group_id
                for item in result.items
                if item.value is not None and item.value.primary_replica_group_id is not None
            )
        )
        current_revisions: dict[ReplicaGroupID, DeploymentRevisionID | Exception | None] = {}
        if group_ids:
            loaded = await self.batch_load_fields(
                self._deployment.bulk_get_replica_groups,
                BulkGetReplicaGroupsAction(ids=group_ids),
                group_ids,
                self._current_revision_of,
            )
            current_revisions = dict(zip(group_ids, loaded, strict=True))
        return [
            self._deployment_with_current_revision(item.value, current_revisions)
            if item.value is not None
            else self.batch_load_failure(item.error)
            for item in result.items
        ]

    def _current_revision_of(self, group: ReplicaGroupData) -> DeploymentRevisionID | None:
        return group.current_revision_id

    def _deployment_with_current_revision(
        self,
        data: ModelDeploymentData,
        current_revisions: Mapping[ReplicaGroupID, DeploymentRevisionID | Exception | None],
    ) -> DeploymentNode | Exception:
        group_id = data.primary_replica_group_id
        current = current_revisions.get(group_id) if group_id is not None else None
        if isinstance(current, Exception):
            return current
        return self._deployment_data_to_dto(
            replace(
                data,
                current_revision_id=current,
                revision_history_ids=[current] if current is not None else [],
            )
        )

    async def batch_load_revisions_by_ids(
        self,
        revision_ids: Sequence[DeploymentRevisionID],
    ) -> list[RevisionNode | Exception | None]:
        """Batch load revisions by ID for DataLoader use, checked per owning deployment."""
        if not revision_ids:
            return []
        ids = [DeploymentRevisionID(revision_id) for revision_id in revision_ids]
        return await self.batch_load_fields(
            self._deployment.bulk_get_revisions,
            BulkGetRevisionsAction(ids=ids),
            ids,
            self._revision_data_to_dto,
        )

    async def batch_load_replicas_by_ids(
        self,
        replica_ids: Sequence[ReplicaID],
    ) -> list[ReplicaNode | Exception | None]:
        """Batch load replicas by ID for DataLoader use, checked per owning deployment."""
        if not replica_ids:
            return []
        ids = [ReplicaID(replica_id) for replica_id in replica_ids]
        return await self.batch_load_fields(
            self._deployment.bulk_get_replicas,
            BulkGetReplicasAction(ids=ids),
            ids,
            self._replica_data_to_dto,
        )

    async def batch_load_routes_by_ids(
        self,
        route_ids: Sequence[uuid.UUID],
    ) -> list[RouteNode | Exception | None]:
        """Batch load routes by ID for DataLoader use, checked per owning deployment."""
        if not route_ids:
            return []
        ids = [ReplicaID(route_id) for route_id in route_ids]
        return await self.batch_load_fields(
            self._deployment.bulk_get_routes,
            BulkGetRoutesAction(ids=ids),
            ids,
            self._route_info_to_dto,
        )

    async def batch_load_access_tokens_by_ids(
        self,
        token_ids: Sequence[DeploymentTokenID],
    ) -> list[AccessTokenNode | Exception | None]:
        """Batch load access tokens by ID for DataLoader use, checked per owning deployment."""
        if not token_ids:
            return []
        ids = [DeploymentTokenID(token_id) for token_id in token_ids]
        return await self.batch_load_fields(
            self._deployment.bulk_get_access_tokens,
            BulkGetAccessTokensAction(ids=ids),
            ids,
            self._access_token_data_to_dto,
        )

    async def batch_load_auto_scaling_rules_by_ids(
        self,
        rule_ids: Sequence[uuid.UUID],
    ) -> list[AutoScalingRuleNode | Exception | None]:
        """Batch load auto-scaling rules by ID for DataLoader use, checked per owning deployment."""
        if not rule_ids:
            return []
        ids = [AutoScalingRuleID(rule_id) for rule_id in rule_ids]
        return await self.batch_load_fields(
            self._deployment.bulk_get_auto_scaling_rules,
            BulkGetAutoScalingRulesAction(ids=ids),
            ids,
            self._auto_scaling_rule_data_to_dto,
        )

    async def batch_load_policies_by_endpoint_ids(
        self,
        endpoint_ids: Sequence[DeploymentID],
    ) -> list[DeploymentPolicyNode | Exception | None]:
        """Batch load deployment policies by deployment ID for DataLoader use.

        One answer per deployment in the given order: the policy, ``None`` for a
        deployment carrying none or an id matching no row, and the denial for one the
        caller may not read.
        """
        if not endpoint_ids:
            return []
        policy_result = await self._deployment.bulk_get_deployment_policies.run(
            BulkGetDeploymentPoliciesAction(
                deployment_ids=[DeploymentID(endpoint_id) for endpoint_id in endpoint_ids]
            )
        )
        return [
            self._policy_data_to_dto(item.value)
            if item.value is not None
            else self.batch_load_failure(item.error)
            for item in policy_result.items
        ]

    # ------------------------------------------------------------------
    # Querier builders
    # ------------------------------------------------------------------

    def _convert_deployment_filter(self, f: DeploymentFilter) -> list[QueryCondition]:
        fields = DeploymentSearchableFields.own
        nested = DeploymentSearchableFields.nested
        conditions: list[QueryCondition] = [
            *self.apply_string_filter(f.name, fields.name.filter),
            *self.apply_string_filter(f.tags, fields.tag.filter),
            *self.apply_string_filter(f.endpoint_url, fields.url.filter),
            *self.apply_string_filter(f.domain_name, fields.domain.filter),
            *self.apply_string_filter(f.resource_group, fields.resource_group.filter),
            *self.apply_uuid_filter(f.project_id, fields.project.filter),
            *self.apply_uuid_filter(f.created_user_id, fields.created_user.filter),
            *self.apply_bool_filter(f.open_to_public, fields.open_to_public.filter),
            *self.apply_datetime_filter(f.created_at, fields.created_at.filter),
            *self.apply_nullable_datetime_filter(f.destroyed_at, fields.destroyed_at.filter),
            *self._convert_deployment_status_filter(f.status),
            *self.apply_uuid_filter(f.entity_id, fields.entity_id.filter),
            *self.apply_int_filter(f.desired_replicas, fields.desired_replicas.filter),
            *self.apply_enum_filter(f.scaling_state, fields.scaling_state.filter),
            *self.apply_to_many_filter(
                f.replicas, nested.replicas.correlation, self._convert_replica_filter
            ),
            *self.apply_to_many_filter(
                f.labels, nested.labels.correlation, self._convert_entity_label_filter
            ),
        ]
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

    def _convert_deployment_status_filter(
        self, status: DeploymentStatusFilter | None
    ) -> list[QueryCondition]:
        """One deployment status covers several lifecycle stages, so it is not an enum filter."""
        if status is None:
            return []
        stages = DeploymentSearchableFields.own.lifecycle_stage.filter
        conditions: list[QueryCondition] = []
        if status.equals is not None:
            if matched := _status_to_lifecycles(status.equals):
                conditions.append(stages.in_(matched))
        if status.in_ is not None:
            if matched := _statuses_to_lifecycles(status.in_):
                conditions.append(stages.in_(matched))
        if status.not_equals is not None:
            if matched := _status_to_lifecycles(status.not_equals):
                conditions.append(stages.not_in(matched))
        if status.not_in is not None:
            if matched := _statuses_to_lifecycles(status.not_in):
                conditions.append(stages.not_in(matched))
        return conditions

    def _build_scoped_deployment_searcher(
        self, input: ScopedSearchDeploymentsInput
    ) -> DeploymentSearcher:
        conditions: list[QueryCondition] = []
        if input.filter:
            conditions.extend(self._convert_deployment_filter(input.filter))
        orders: list[QueryOrder] = (
            self._convert_deployment_orders(input.order) if input.order else []
        )
        return self._build_searcher(
            DeploymentSearcher,
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

    def _build_deployment_searcher(self, input: AdminSearchDeploymentsInput) -> DeploymentSearcher:
        conditions: list[QueryCondition] = []
        if input.filter:
            conditions.extend(self._convert_deployment_filter(input.filter))
        orders: list[QueryOrder] = (
            self._convert_deployment_orders(input.order) if input.order else []
        )
        return self._build_searcher(
            DeploymentSearcher,
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
        fields = ModelRevisionSearchableFields.own
        conditions: list[QueryCondition] = [
            *self.apply_int_filter(f.revision_number, fields.revision_number.filter),
            *self.apply_uuid_filter(f.image_id, fields.image.filter),
            *self.apply_uuid_filter(f.model_vfolder_id, fields.model.filter),
            *self.apply_string_filter(f.resource_group, fields.resource_group.filter),
            *self.apply_string_filter(f.cluster_mode, fields.cluster_mode.filter),
            *self.apply_uuid_filter(f.runtime_variant_id, fields.runtime_variant_id.filter),
            *self.apply_uuid_filter(f.field_id, fields.field_id.filter),
            *self.apply_string_filter(
                f.model_mount_destination, fields.model_mount_destination.filter
            ),
            *self.apply_string_filter(f.vfolder_subpath, fields.vfolder_subpath.filter),
            *self.apply_string_filter(f.model_definition_path, fields.model_definition_path.filter),
            *self.apply_int_filter(f.cluster_size, fields.cluster_size.filter),
            *self.apply_uuid_filter(f.revision_preset_id, fields.revision_preset_id.filter),
            *self.apply_datetime_filter(f.created_at, fields.created_at.filter),
        ]
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

    def _build_revision_searcher(self, input: AdminSearchRevisionsInput) -> ModelRevisionSearcher:
        """The filters and page of a revision search whose deployment the action scopes."""
        conditions: list[QueryCondition] = (
            self._convert_revision_filter(input.filter) if input.filter else []
        )
        orders: list[QueryOrder] = self._convert_revision_orders(input.order) if input.order else []
        return self._build_searcher(
            ModelRevisionSearcher,
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
        fields = ReplicaSearchableFields.own
        conditions: list[QueryCondition] = []
        if f.status is not None:
            conditions.append(
                fields.status.filter.in_([ManagerRouteStatus(s.value) for s in f.status])
            )
        if f.health_status is not None:
            conditions.append(
                fields.health_status.filter.in_([
                    ManagerRouteHealthStatus(s.value) for s in f.health_status
                ])
            )
        if f.traffic_status is not None:
            conditions.append(
                fields.traffic_status.filter.in_([
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
        scope: RouteOperationScope | None = None,
    ) -> BatchQuerier:
        conditions: list[QueryCondition] = []
        if scope is not None:
            conditions.append(
                ReplicaSearchableFields.own.deployment_id.filter.equals(
                    UUIDEqualMatchSpec(value=scope.deployment_id, negated=False)
                )
            )
        if input.filter:
            f = input.filter
            if scope is None and f.deployment_id is not None:
                conditions.append(
                    ReplicaSearchableFields.own.deployment_id.filter.equals(
                        UUIDEqualMatchSpec(value=f.deployment_id, negated=False)
                    )
                )
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
        fields = DeploymentAccessTokenSearchableFields.own
        conditions: list[QueryCondition] = [
            *self.apply_datetime_filter(f.expires_at, fields.expires_at.filter),
            *self.apply_datetime_filter(f.created_at, fields.created_at.filter),
            *self.apply_uuid_filter(f.field_id, fields.field_id.filter),
        ]
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

    def _convert_auto_scaling_rule_filter(self, f: AutoScalingRuleFilter) -> list[QueryCondition]:
        fields = AutoScalingRuleSearchableFields.own
        conditions: list[QueryCondition] = [
            *self.apply_datetime_filter(f.created_at, fields.created_at.filter),
            *self.apply_nullable_datetime_filter(
                f.last_triggered_at, fields.last_triggered_at.filter
            ),
            *self.apply_uuid_filter(f.field_id, fields.field_id.filter),
            *self.apply_enum_filter(f.metric_source, fields.metric_source.filter),
            *self.apply_string_filter(f.metric_name, fields.metric_name.filter),
            *self.apply_decimal_filter(f.min_threshold, fields.min_threshold.filter),
            *self.apply_decimal_filter(f.max_threshold, fields.max_threshold.filter),
            *self.apply_int_filter(f.step_size, fields.step_size.filter),
            *self.apply_int_filter(f.time_window, fields.cooldown_seconds.filter),
            *self.apply_int_filter(f.min_replicas, fields.min_replicas.filter),
            *self.apply_int_filter(f.max_replicas, fields.max_replicas.filter),
            *self.apply_uuid_filter(
                f.prometheus_query_preset_id, fields.prometheus_query_preset_id.filter
            ),
        ]
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
        scope: AutoScalingRuleOperationScope | None = None,
    ) -> BatchQuerier:
        conditions: list[QueryCondition] = []
        if scope is not None:
            conditions.append(
                AutoScalingRuleSearchableFields.own.deployment_id.filter.equals(
                    UUIDEqualMatchSpec(value=scope.deployment_id, negated=False)
                )
            )
        elif input.filter and input.filter.deployment_id is not None:
            conditions.append(
                AutoScalingRuleSearchableFields.own.deployment_id.filter.equals(
                    UUIDEqualMatchSpec(value=input.filter.deployment_id, negated=False)
                )
            )
        if input.filter:
            conditions.extend(self._convert_auto_scaling_rule_filter(input.filter))
        orders: list[QueryOrder] = (
            [self._convert_auto_scaling_rule_order(o) for o in input.order] if input.order else []
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
                DeploymentPolicySearchableFields.own.endpoint.filter.equals(
                    UUIDEqualMatchSpec(value=input.filter.deployment_id, negated=False)
                )
            )
        return self._build_querier(
            conditions=conditions,
            orders=[],
            pagination_spec=_get_deployment_policy_pagination_spec(),
            limit=input.limit,
            offset=input.offset,
        )

    def _convert_replica_filter(self, f: ReplicaFilter) -> list[QueryCondition]:
        fields = ReplicaSearchableFields.own
        conditions: list[QueryCondition] = [
            *self.apply_enum_filter(f.status, fields.status.filter),
            *self.apply_enum_filter(f.health_status, fields.health_status.filter),
            *self.apply_enum_filter(f.traffic_status, fields.traffic_status.filter),
            *self.apply_datetime_filter(f.created_at, fields.created_at.filter),
            *self.apply_uuid_filter(f.field_id, fields.field_id.filter),
            *self.apply_uuid_filter(f.session_id, fields.session.filter),
            *self.apply_uuid_filter(f.revision_id, fields.revision.filter),
        ]
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

    def _build_access_token_searcher(
        self, input: SearchAccessTokensInput
    ) -> DeploymentAccessTokenSearcher:
        """The filters and page of a token search whose deployment the action scopes."""
        conditions: list[QueryCondition] = (
            self._convert_access_token_filter(input.filter) if input.filter else []
        )
        orders: list[QueryOrder] = (
            [self._convert_access_token_order(o) for o in input.order] if input.order else []
        )
        return self._build_searcher(
            DeploymentAccessTokenSearcher,
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

    def _build_replica_searcher(self, input: SearchReplicasInput) -> ModelReplicaSearcher:
        """The filters and page of a replica search whose deployment the action scopes."""
        conditions: list[QueryCondition] = (
            self._convert_replica_filter(input.filter) if input.filter else []
        )
        orders: list[QueryOrder] = self._convert_replica_orders(input.order) if input.order else []
        return self._build_searcher(
            ModelReplicaSearcher,
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

    @staticmethod
    def _convert_tag_state(tags: list[str] | None | Unset) -> TriState[str]:
        if isinstance(tags, Unset):
            return TriState.nop()
        if tags is None:
            return TriState.nullify()
        return TriState.update(",".join(tags))

    # ------------------------------------------------------------------
    # Order converters
    # ------------------------------------------------------------------

    def _convert_deployment_orders(self, orders: list[DeploymentOrder]) -> list[QueryOrder]:
        return [self._convert_deployment_order(order) for order in orders]

    def _convert_deployment_order(self, order: DeploymentOrder) -> QueryOrder:
        fields = DeploymentSearchableFields.own
        ascending = order.direction == OrderDirection.ASC
        match order.field:
            case DeploymentOrderField.NAME:
                return fields.name.order.apply(ascending)
            case DeploymentOrderField.CREATED_AT:
                return fields.created_at.order.apply(ascending)
            case DeploymentOrderField.DESTROYED_AT:
                return fields.destroyed_at.order.apply(ascending)
            case DeploymentOrderField.DOMAIN:
                return fields.domain.order.apply(ascending)
            case DeploymentOrderField.PROJECT:
                return fields.project.order.apply(ascending)
            case DeploymentOrderField.RESOURCE_GROUP:
                return fields.resource_group.order.apply(ascending)
            case DeploymentOrderField.TAG:
                return fields.tag.order.apply(ascending)
            case DeploymentOrderField.ENTITY_ID:
                return fields.entity_id.order.apply(ascending)
            case DeploymentOrderField.DESIRED_REPLICAS:
                return fields.desired_replicas.order.apply(ascending)
            case DeploymentOrderField.SCALING_STATE:
                return fields.scaling_state.order.apply(ascending)
            case DeploymentOrderField.CREATED_USER_ID:
                return fields.created_user.order.apply(ascending)
            case DeploymentOrderField.OPEN_TO_PUBLIC:
                return fields.open_to_public.order.apply(ascending)
            case DeploymentOrderField.ENDPOINT_URL:
                return fields.url.order.apply(ascending)
            case _:
                assert_never(order.field)

    def _convert_revision_orders(self, orders: list[RevisionOrder]) -> list[QueryOrder]:
        return [self._convert_revision_order(order) for order in orders]

    def _convert_revision_order(self, order: RevisionOrder) -> QueryOrder:
        fields = ModelRevisionSearchableFields.own
        ascending = order.direction == OrderDirection.ASC
        match order.field:
            case RevisionOrderField.REVISION_NUMBER:
                return fields.revision_number.order.apply(ascending)
            case RevisionOrderField.CREATED_AT:
                return fields.created_at.order.apply(ascending)
            case RevisionOrderField.RESOURCE_GROUP:
                return fields.resource_group.order.apply(ascending)
            case RevisionOrderField.CLUSTER_MODE:
                return fields.cluster_mode.order.apply(ascending)
            case RevisionOrderField.RUNTIME_VARIANT_NAME:
                variant = ModelRevisionSearchableFields.nested.runtime_variant
                return variant.correlation.order(variant.fields.name.column).apply(ascending)
            case RevisionOrderField.FIELD_ID:
                return fields.field_id.order.apply(ascending)
            case RevisionOrderField.DEPLOYMENT_ID:
                return fields.deployment_id.order.apply(ascending)
            case RevisionOrderField.IMAGE_ID:
                return fields.image.order.apply(ascending)
            case RevisionOrderField.MODEL_VFOLDER_ID:
                return fields.model.order.apply(ascending)
            case RevisionOrderField.MODEL_MOUNT_DESTINATION:
                return fields.model_mount_destination.order.apply(ascending)
            case RevisionOrderField.VFOLDER_SUBPATH:
                return fields.vfolder_subpath.order.apply(ascending)
            case RevisionOrderField.MODEL_DEFINITION_PATH:
                return fields.model_definition_path.order.apply(ascending)
            case RevisionOrderField.CLUSTER_SIZE:
                return fields.cluster_size.order.apply(ascending)
            case RevisionOrderField.REVISION_PRESET_ID:
                return fields.revision_preset_id.order.apply(ascending)
            case _:
                assert_never(order.field)

    def _convert_route_orders(self, orders: list[RouteOrder]) -> list[QueryOrder]:
        return [self._convert_route_order(order) for order in orders]

    def _convert_route_order(self, order: RouteOrder) -> QueryOrder:
        fields = ReplicaSearchableFields.own
        ascending = order.direction == OrderDirection.ASC
        match order.field:
            case RouteOrderField.CREATED_AT:
                return fields.created_at.order.apply(ascending)
            case RouteOrderField.STATUS:
                return fields.status.order.apply(ascending)
            case RouteOrderField.TRAFFIC_RATIO:
                return fields.traffic_ratio.order.apply(ascending)
            case _:
                assert_never(order.field)

    def _convert_access_token_order(self, order: AccessTokenOrder) -> QueryOrder:
        fields = DeploymentAccessTokenSearchableFields.own
        ascending = order.direction == OrderDirection.ASC
        match order.field:
            case AccessTokenOrderField.CREATED_AT:
                return fields.created_at.order.apply(ascending)
            case AccessTokenOrderField.FIELD_ID:
                return fields.field_id.order.apply(ascending)
            case AccessTokenOrderField.EXPIRES_AT:
                return fields.expires_at.order.apply(ascending)
            case _:
                assert_never(order.field)

    def _convert_auto_scaling_rule_order(self, order: AutoScalingRuleOrder) -> QueryOrder:
        fields = AutoScalingRuleSearchableFields.own
        ascending = order.direction == OrderDirection.ASC
        match order.field:
            case AutoScalingRuleOrderField.CREATED_AT:
                return fields.created_at.order.apply(ascending)
            case AutoScalingRuleOrderField.FIELD_ID:
                return fields.field_id.order.apply(ascending)
            case AutoScalingRuleOrderField.METRIC_SOURCE:
                return fields.metric_source.order.apply(ascending)
            case AutoScalingRuleOrderField.METRIC_NAME:
                return fields.metric_name.order.apply(ascending)
            case AutoScalingRuleOrderField.MIN_THRESHOLD:
                return fields.min_threshold.order.apply(ascending)
            case AutoScalingRuleOrderField.MAX_THRESHOLD:
                return fields.max_threshold.order.apply(ascending)
            case AutoScalingRuleOrderField.STEP_SIZE:
                return fields.step_size.order.apply(ascending)
            case AutoScalingRuleOrderField.TIME_WINDOW:
                return fields.cooldown_seconds.order.apply(ascending)
            case AutoScalingRuleOrderField.MIN_REPLICAS:
                return fields.min_replicas.order.apply(ascending)
            case AutoScalingRuleOrderField.MAX_REPLICAS:
                return fields.max_replicas.order.apply(ascending)
            case AutoScalingRuleOrderField.PROMETHEUS_QUERY_PRESET_ID:
                return fields.prometheus_query_preset_id.order.apply(ascending)
            case AutoScalingRuleOrderField.LAST_TRIGGERED_AT:
                return fields.last_triggered_at.order.apply(ascending)
            case _:
                assert_never(order.field)

    def _convert_replica_orders(self, orders: list[ReplicaOrder]) -> list[QueryOrder]:
        return [self._convert_replica_order(order) for order in orders]

    def _convert_replica_order(self, order: ReplicaOrder) -> QueryOrder:
        fields = ReplicaSearchableFields.own
        ascending = order.direction == OrderDirection.ASC
        match order.field:
            case ReplicaOrderField.CREATED_AT:
                return fields.created_at.order.apply(ascending)
            case ReplicaOrderField.ID:
                return fields.field_id.order.apply(ascending)
            case ReplicaOrderField.DEPLOYMENT_ID:
                return fields.deployment_id.order.apply(ascending)
            case ReplicaOrderField.SESSION_ID:
                return fields.session.order.apply(ascending)
            case ReplicaOrderField.REVISION_ID:
                return fields.revision.order.apply(ascending)
            case ReplicaOrderField.STATUS:
                return fields.status.order.apply(ascending)
            case ReplicaOrderField.TRAFFIC_STATUS:
                return fields.traffic_status.order.apply(ascending)
            case ReplicaOrderField.HEALTH_STATUS:
                return fields.health_status.order.apply(ascending)
            case _:
                assert_never(order.field)

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
            entity_id=data.entity_id(),
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
            field_id=data.id,
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
                runtime_variant_preset_values=[
                    RuntimeVariantPresetValueInfoDTO(preset_id=pv.preset_id, value=pv.value)
                    for pv in data.model_runtime_config.runtime_variant_preset_values
                ],
            ),
            model_mount_config=model_mount_config_dto,
            model_definition=_model_definition_to_dto(data.model_definition),
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
            revision_preset_id=data.revision_preset.preset_id,
        )

    @staticmethod
    def _route_info_to_dto(data: RouteInfo) -> RouteNode:
        return RouteNode(
            id=data.route_id,
            field_id=data.route_id,
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
            field_id=data.id,
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
            field_id=data.id,
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
            field_id=data.id,
            deployment_id=data.endpoint,
            strategy_spec=strategy_spec,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )

    @staticmethod
    def _replica_data_to_dto(data: ModelReplicaData) -> ReplicaNode:
        return ReplicaNode(
            id=data.id,
            field_id=data.id,
            deployment_id=data.deployment_id,
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
