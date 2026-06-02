"""Deployment service for managing model deployments."""

import logging
from datetime import UTC, datetime
from typing import cast
from uuid import UUID

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.model_deployment.types import (
    ActivenessStatus,
    DeploymentStrategy,
    LivenessStatus,
    ModelDeploymentStatus,
    ReadinessStatus,
)
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.request import (
    MintEndpointTokenRequest,
)
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.clients.appproxy.client import AppProxyClientPool
from ai.backend.manager.data.deployment.creator import (
    ModelRevisionCreator,
    VFolderMountsCreator,
)
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    ExecutionSpec,
    LegacyDeploymentData,
    ModelDeploymentAccessTokenData,
    ModelDeploymentData,
    ModelDeploymentMetadataInfo,
    ModelReplicaData,
    ModelRevisionData,
    MountInfo,
    ReplicaStateData,
    ResourceSpec,
    RevisionRefreshResult,
    RouteHealthStatus,
    RouteInfo,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.service import RoutingNotFound
from ai.backend.manager.models.deployment_policy import (
    DeploymentPolicyRow,
)
from ai.backend.manager.models.endpoint import EndpointTokenRow
from ai.backend.manager.models.endpoint.conditions import DeploymentConditions
from ai.backend.manager.repositories.base import BatchQuerier, NoPagination
from ai.backend.manager.repositories.base.rbac.entity_creator import RBACEntityCreator
from ai.backend.manager.repositories.base.upserter import Upserter
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.repositories.deployment.creators import (
    EndpointTokenCreatorSpec,
)
from ai.backend.manager.repositories.deployment.updaters import DeploymentUpdaterSpec
from ai.backend.manager.repositories.deployment.upserters import DeploymentPolicyUpserterSpec
from ai.backend.manager.repositories.deployment_revision_preset.repository import (
    DeploymentRevisionPresetRepository,
)
from ai.backend.manager.repositories.runtime_variant_preset.repository import (
    RuntimeVariantPresetRepository,
)
from ai.backend.manager.services.deployment.actions.access_token.bulk_delete_access_tokens import (
    BulkDeleteAccessTokensAction,
    BulkDeleteAccessTokensActionResult,
)
from ai.backend.manager.services.deployment.actions.access_token.create_access_token import (
    CreateAccessTokenAction,
    CreateAccessTokenActionResult,
)
from ai.backend.manager.services.deployment.actions.access_token.delete_access_token import (
    DeleteAccessTokenAction,
    DeleteAccessTokenActionResult,
)
from ai.backend.manager.services.deployment.actions.access_token.get_access_token import (
    GetAccessTokenAction,
    GetAccessTokenActionResult,
)
from ai.backend.manager.services.deployment.actions.access_token.search_access_tokens import (
    SearchAccessTokensAction,
    SearchAccessTokensActionResult,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.bulk_delete_auto_scaling_rules import (
    BulkDeleteAutoScalingRulesAction,
    BulkDeleteAutoScalingRulesActionResult,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.create_auto_scaling_rule import (
    CreateAutoScalingRuleAction,
    CreateAutoScalingRuleActionResult,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.delete_auto_scaling_rule import (
    DeleteAutoScalingRuleAction,
    DeleteAutoScalingRuleActionResult,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.get_auto_scaling_rule import (
    GetAutoScalingRuleAction,
    GetAutoScalingRuleActionResult,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.search_auto_scaling_rules import (
    SearchAutoScalingRulesAction,
    SearchAutoScalingRulesActionResult,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.update_auto_scaling_rule import (
    UpdateAutoScalingRuleAction,
    UpdateAutoScalingRuleActionResult,
)
from ai.backend.manager.services.deployment.actions.create_deployment import (
    CreateDeploymentAction,
    CreateDeploymentActionResult,
)
from ai.backend.manager.services.deployment.actions.create_legacy_deployment import (
    CreateLegacyDeploymentAction,
    CreateLegacyDeploymentActionResult,
)
from ai.backend.manager.services.deployment.actions.deployment_policy import (
    GetDeploymentPolicyAction,
    GetDeploymentPolicyActionResult,
    SearchDeploymentPoliciesAction,
    SearchDeploymentPoliciesActionResult,
    UpsertDeploymentPolicyAction,
    UpsertDeploymentPolicyActionResult,
)
from ai.backend.manager.services.deployment.actions.destroy_deployment import (
    DestroyDeploymentAction,
    DestroyDeploymentActionResult,
)
from ai.backend.manager.services.deployment.actions.get_deployment_by_id import (
    GetDeploymentByIdAction,
    GetDeploymentByIdActionResult,
)
from ai.backend.manager.services.deployment.actions.get_legacy_deployment_by_id import (
    GetLegacyDeploymentByIdAction,
    GetLegacyDeploymentByIdActionResult,
)
from ai.backend.manager.services.deployment.actions.get_replica_by_id import (
    GetReplicaByIdAction,
    GetReplicaByIdActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.add_model_revision import (
    AddModelRevisionAction,
    AddModelRevisionActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.get_revision_by_id import (
    GetRevisionByIdAction,
    GetRevisionByIdActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.search_revision_resource_slots import (
    SearchRevisionResourceSlotsAction,
    SearchRevisionResourceSlotsActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.search_revisions import (
    SearchRevisionsAction,
    SearchRevisionsActionResult,
)
from ai.backend.manager.services.deployment.actions.refresh_deployment_revisions import (
    RefreshDeploymentRevisionsAction,
    RefreshDeploymentRevisionsActionResult,
)
from ai.backend.manager.services.deployment.actions.replace_deployment_options import (
    ReplaceDeploymentOptionsAction,
    ReplaceDeploymentOptionsActionResult,
)
from ai.backend.manager.services.deployment.actions.revision_operations import (
    ActivateRevisionAction,
    ActivateRevisionActionResult,
)
from ai.backend.manager.services.deployment.actions.route import (
    SearchRoutesAction,
    SearchRoutesActionResult,
    UpdateRouteTrafficStatusAction,
    UpdateRouteTrafficStatusActionResult,
)
from ai.backend.manager.services.deployment.actions.search_deployments import (
    SearchDeploymentsAction,
    SearchDeploymentsActionResult,
)
from ai.backend.manager.services.deployment.actions.search_deployments_in_project import (
    SearchDeploymentsInProjectAction,
    SearchDeploymentsInProjectActionResult,
)
from ai.backend.manager.services.deployment.actions.search_legacy_deployments import (
    SearchLegacyDeploymentsAction,
    SearchLegacyDeploymentsActionResult,
)
from ai.backend.manager.services.deployment.actions.search_replicas import (
    SearchReplicasAction,
    SearchReplicasActionResult,
)
from ai.backend.manager.services.deployment.actions.sync_replicas import (
    SyncReplicaAction,
    SyncReplicaActionResult,
)
from ai.backend.manager.services.deployment.actions.update_deployment import (
    UpdateDeploymentAction,
    UpdateDeploymentActionResult,
)
from ai.backend.manager.sokovan.deployment import DeploymentController
from ai.backend.manager.sokovan.deployment.types import DeploymentLifecycleType

log = BraceStyleAdapter(logging.getLogger(__name__))


def _map_lifecycle_to_status(lifecycle: EndpointLifecycle) -> ModelDeploymentStatus:
    """Map EndpointLifecycle to ModelDeploymentStatus for the v2 status surface.

    The lifecycle axis is monotonic (PENDING → DEPLOYING → READY → DESTROYING
    → DESTROYED); v2 exposes replica reconciliation as the orthogonal
    ``scaling_state`` field on the deployment node. ``SCALING`` is therefore
    no longer surfaced through ``ModelDeploymentStatus`` — a legacy
    ``lifecycle=SCALING`` row folds into ``READY`` so clients only have to
    consult ``scaling_state`` to decide whether a replica reconcile is in
    flight. Legacy ``CREATED`` (never-deployed) folds into ``PENDING``.
    """
    match lifecycle:
        case EndpointLifecycle.PENDING | EndpointLifecycle.CREATED:
            return ModelDeploymentStatus.PENDING
        case EndpointLifecycle.READY | EndpointLifecycle.SCALING:
            return ModelDeploymentStatus.READY
        case EndpointLifecycle.DEPLOYING:
            return ModelDeploymentStatus.DEPLOYING
        case EndpointLifecycle.DESTROYING:
            return ModelDeploymentStatus.STOPPING
        case EndpointLifecycle.DESTROYED:
            return ModelDeploymentStatus.STOPPED


def _deployment_desired_replica_count(info: DeploymentInfo) -> int:
    desired_count = info.replica.desired_replica_count
    if desired_count is None:
        desired_count = info.replica.replica_count
    return desired_count


def _convert_deployment_info_to_data(info: DeploymentInfo) -> ModelDeploymentData:
    """Convert DeploymentInfo to the modern (v2 / GraphQL) ModelDeploymentData.

    Uses the revision *ids* only — the modern read path does not load the full
    revision rows. Note: some fields default as DeploymentInfo lacks the data.
    """
    return ModelDeploymentData(
        id=info.id,
        metadata=ModelDeploymentMetadataInfo(
            name=info.metadata.name,
            status=_map_lifecycle_to_status(info.state.lifecycle),
            tags=[info.metadata.tag] if info.metadata.tag else [],
            project_id=info.metadata.project,
            domain_name=info.metadata.domain,
            resource_group_name=info.metadata.resource_group,
            created_at=info.metadata.created_at or datetime.now(UTC),
            updated_at=info.metadata.created_at or datetime.now(UTC),
        ),
        network_access=info.network,
        revision_history_ids=[info.current_revision_id]
        if info.current_revision_id is not None
        else [],
        current_revision_id=info.current_revision_id,
        deploying_revision_id=info.deploying_revision_id,
        scaling_rule_ids=[],  # Not available in DeploymentInfo
        replica_state=ReplicaStateData(
            desired_replica_count=_deployment_desired_replica_count(info),
            replica_ids=[],  # Not available in DeploymentInfo
        ),
        default_deployment_strategy=DeploymentStrategy.ROLLING,
        created_user_id=info.metadata.created_user,
        options=info.options,
        scaling_state=info.state.scaling_state,
        policy=info.policy,
        sub_step=info.sub_step,
    )


def _convert_deployment_info_to_legacy_data(info: DeploymentInfo) -> LegacyDeploymentData:
    """Convert DeploymentInfo to the legacy (REST v1) LegacyDeploymentData.

    Built independently from the same ``DeploymentInfo`` — never derived from
    ``ModelDeploymentData``. Carries the full current ``revision`` that the
    legacy ``DeploymentDTO`` embeds, so it requires a full (legacy) read.
    """
    return LegacyDeploymentData(
        id=info.id,
        metadata=ModelDeploymentMetadataInfo(
            name=info.metadata.name,
            status=_map_lifecycle_to_status(info.state.lifecycle),
            tags=[info.metadata.tag] if info.metadata.tag else [],
            project_id=info.metadata.project,
            domain_name=info.metadata.domain,
            resource_group_name=info.metadata.resource_group,
            created_at=info.metadata.created_at or datetime.now(UTC),
            updated_at=info.metadata.created_at or datetime.now(UTC),
        ),
        network_access=info.network,
        revision=info.current_revision,
        replica_state=ReplicaStateData(
            desired_replica_count=_deployment_desired_replica_count(info),
            replica_ids=[],  # Not available in DeploymentInfo
        ),
        default_deployment_strategy=DeploymentStrategy.ROLLING,
        created_user_id=info.metadata.created_user,
        policy=info.policy,
        sub_step=info.sub_step,
    )


_HEALTH_STATUS_TO_READINESS: dict[RouteHealthStatus, ReadinessStatus] = {
    RouteHealthStatus.HEALTHY: ReadinessStatus.HEALTHY,
    RouteHealthStatus.UNHEALTHY: ReadinessStatus.UNHEALTHY,
    RouteHealthStatus.DEGRADED: ReadinessStatus.UNHEALTHY,
    RouteHealthStatus.NOT_CHECKED: ReadinessStatus.NOT_CHECKED,
}

_ROUTE_STATUS_TO_LIVENESS: dict[RouteStatus, LivenessStatus] = {
    RouteStatus.RUNNING: LivenessStatus.HEALTHY,
    RouteStatus.PROVISIONING: LivenessStatus.NOT_CHECKED,
    RouteStatus.TERMINATING: LivenessStatus.DEGRADED,
    RouteStatus.TERMINATED: LivenessStatus.UNHEALTHY,
    RouteStatus.FAILED_TO_START: LivenessStatus.UNHEALTHY,
}


def _resolve_activeness(
    traffic_status: RouteTrafficStatus,
    readiness: ReadinessStatus,
    liveness: LivenessStatus,
) -> ActivenessStatus:
    """Determine activeness from traffic_status, readiness, and liveness.

    A replica is ACTIVE only when:
    - traffic_status is ACTIVE (admin hasn't disabled it), AND
    - readiness is HEALTHY (health check passed), AND
    - liveness is HEALTHY (container is running)
    """
    if traffic_status != RouteTrafficStatus.ACTIVE:
        return ActivenessStatus.INACTIVE
    if readiness != ReadinessStatus.HEALTHY:
        return ActivenessStatus.INACTIVE
    if liveness != LivenessStatus.HEALTHY:
        return ActivenessStatus.INACTIVE
    return ActivenessStatus.ACTIVE


def _convert_route_info_to_replica_data(route: RouteInfo) -> ModelReplicaData:
    """Convert RouteInfo to ModelReplicaData."""
    readiness = _HEALTH_STATUS_TO_READINESS.get(route.health_status) or ReadinessStatus.NOT_CHECKED
    liveness = _ROUTE_STATUS_TO_LIVENESS.get(route.status) or LivenessStatus.NOT_CHECKED
    return ModelReplicaData(
        id=route.route_id,
        revision_id=route.revision_id or route.deployment_id,
        session_id=route.session_id,
        readiness_status=readiness,
        liveness_status=liveness,
        activeness_status=_resolve_activeness(route.traffic_status, readiness, liveness),
        status=route.status,
        traffic_status=route.traffic_status,
        health_status=route.health_status,
        detail=route.error_data,
        created_at=route.created_at,
    )


def _build_creator_from_revision_data(data: ModelRevisionData) -> ModelRevisionCreator:
    """Rebuild a ``ModelRevisionCreator`` from a persisted revision.

    ``model_definition`` is cleared so ``add_revision`` re-resolves it via
    the merge chain. Mount identity (``extra_mounts``, ``vfolder_subpath``)
    is copied verbatim — refreshing must not silently drop them.
    """
    if data.model_mount_config.vfolder_id is None:
        raise InvalidAPIParameters(
            f"Revision {data.id} has no model vfolder; cannot rebuild creator"
        )
    return ModelRevisionCreator(
        image_id=data.image_id,
        resource_spec=ResourceSpec(
            cluster_mode=data.cluster_config.mode,
            cluster_size=data.cluster_config.size,
            resource_slots=dict(data.resource_config.resource_slot),
            resource_opts=dict(data.resource_config.resource_opts) or None,
        ),
        mounts=VFolderMountsCreator(
            model_vfolder_id=data.model_mount_config.vfolder_id,
            model_definition_path=data.model_mount_config.definition_path or None,
            model_mount_destination=data.model_mount_config.mount_destination or "/models",
            extra_mounts=[
                MountInfo(
                    vfolder_id=m.vfolder_id,
                    mount_destination=m.mount_destination,
                    mount_perm=m.mount_perm,
                    subpath=m.subpath,
                )
                for m in data.model_mount_config.extra_mounts
            ],
            vfolder_subpath=data.model_mount_config.subpath,
        ),
        execution=ExecutionSpec(
            startup_command=data.execution.startup_command,
            bootstrap_script=data.execution.bootstrap_script,
            environ=(
                {k: str(v) for k, v in data.model_runtime_config.environ.items()}
                if data.model_runtime_config.environ
                else None
            ),
            runtime_variant_id=data.model_runtime_config.runtime_variant_id,
            callback_url=data.execution.callback_url,
            inference_runtime_config=data.model_runtime_config.inference_runtime_config,
        ),
        model_definition=None,
        revision_preset_id=data.preset.preset_id,
        preset_values=list(data.preset.values),
    )


class DeploymentService:
    """Service for managing deployments."""

    _deployment_controller: DeploymentController
    _deployment_repository: DeploymentRepository
    _appproxy_client_pool: AppProxyClientPool
    _deployment_revision_preset_repository: DeploymentRevisionPresetRepository | None
    _runtime_variant_preset_repository: RuntimeVariantPresetRepository | None

    def __init__(
        self,
        deployment_controller: DeploymentController,
        deployment_repository: DeploymentRepository,
        appproxy_client_pool: AppProxyClientPool,
        deployment_revision_preset_repository: DeploymentRevisionPresetRepository | None = None,
        runtime_variant_preset_repository: RuntimeVariantPresetRepository | None = None,
    ) -> None:
        """Initialize deployment service with controller and repository."""
        self._deployment_controller = deployment_controller
        self._deployment_repository = deployment_repository
        self._appproxy_client_pool = appproxy_client_pool
        self._deployment_revision_preset_repository = deployment_revision_preset_repository
        self._runtime_variant_preset_repository = runtime_variant_preset_repository

    # ========== Deployment CRUD ==========

    async def create_deployment(
        self, action: CreateDeploymentAction
    ) -> CreateDeploymentActionResult:
        """Create a new deployment.

        Args:
            action: Create deployment action containing the creator specification

        Returns:
            CreateDeploymentActionResult: Result containing the created deployment data
        """
        log.info("Creating deployment with name: {}", action.creator.metadata.name)
        deployment_info = await self._deployment_controller.create_deployment(action.creator)
        if action.creator.model_revision is not None:
            await self._deployment_controller.add_deployment_revision(
                deployment_id=DeploymentID(deployment_info.id),
                revision=action.creator.model_revision,
                auto_activate=action.auto_activate,
            )
        updated_deployment_info = await self._deployment_repository.get_endpoint_info(
            deployment_info.id
        )
        return CreateDeploymentActionResult(
            data=_convert_deployment_info_to_data(updated_deployment_info)
        )

    async def create_legacy_deployment(
        self, action: CreateLegacyDeploymentAction
    ) -> CreateLegacyDeploymentActionResult:
        """Create a new legacy deployment(Model Serving).

        Args:
            action: Create legacy deployment action containing the creator specification

        Returns:
            CreateLegacyDeploymentActionResult: Result containing the created deployment info
        """
        log.info("Creating deployment with name: {}", action.draft.name)
        creator, revision = await self._deployment_controller.build_creator_from_legacy_draft(
            action.draft
        )
        deployment_info = await self._deployment_controller.create_deployment(creator)
        await self._deployment_controller.add_deployment_revision(
            deployment_id=DeploymentID(deployment_info.id),
            revision=revision,
            auto_activate=True,
        )
        deployment_info = await self._deployment_repository.get_endpoint_info(deployment_info.id)
        return CreateLegacyDeploymentActionResult(data=deployment_info)

    async def update_deployment(
        self, action: UpdateDeploymentAction
    ) -> UpdateDeploymentActionResult:
        """Update an existing deployment.

        Args:
            action: Update deployment action containing the updater

        Returns:
            UpdateDeploymentActionResult: Result containing the updated deployment data
        """
        log.info("Updating deployment with ID: {}", action.updater.pk_value)
        endpoint_id = DeploymentID(cast(UUID, action.updater.pk_value))
        spec = cast(DeploymentUpdaterSpec, action.updater.spec)
        deployment_info = await self._deployment_controller.update_deployment(endpoint_id, spec)
        return UpdateDeploymentActionResult(data=_convert_deployment_info_to_data(deployment_info))

    async def replace_deployment_options(
        self, action: ReplaceDeploymentOptionsAction
    ) -> ReplaceDeploymentOptionsActionResult:
        """Replace the ``options`` surface of a deployment in full.

        The repository returns the persisted :class:`DeploymentOptions`
        via ``UPDATE ... RETURNING`` so this path does a single round-trip
        and does not re-materialise the surrounding deployment node.
        """
        log.info("Replacing deployment options for ID: {}", action.deployment_id)
        options = await self._deployment_repository.replace_deployment_options(
            action.deployment_id, action.options
        )
        return ReplaceDeploymentOptionsActionResult(
            deployment_id=action.deployment_id,
            options=options,
        )

    async def destroy_deployment(
        self, action: DestroyDeploymentAction
    ) -> DestroyDeploymentActionResult:
        """Destroy an existing deployment.

        Args:
            action: Destroy deployment action containing the endpoint ID

        Returns:
            DestroyDeploymentActionResult: Result indicating success or failure

        Raises:
            EndpointNotFound: If the endpoint does not exist
        """
        log.info("Destroying deployment with ID: {}", action.deployment_id)
        # Validate endpoint exists before attempting destruction
        await self._deployment_repository.get_endpoint_info(action.deployment_id)
        success = await self._deployment_controller.destroy_deployment(action.deployment_id)
        await self._deployment_controller.mark_lifecycle_needed(DeploymentLifecycleType.DESTROYING)
        return DestroyDeploymentActionResult(success=success)

    async def search_deployments(
        self, action: SearchDeploymentsAction
    ) -> SearchDeploymentsActionResult:
        """Search deployments with filtering and pagination.

        Args:
            action: Action containing BatchQuerier for filtering and pagination

        Returns:
            SearchDeploymentsActionResult: Result containing list of deployments and pagination info
        """
        result = await self._deployment_repository.search_endpoints(action.querier)
        deployments = [_convert_deployment_info_to_data(info) for info in result.items]
        return SearchDeploymentsActionResult(
            data=deployments,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def search_legacy_deployments(
        self, action: SearchLegacyDeploymentsAction
    ) -> SearchLegacyDeploymentsActionResult:
        """Legacy (REST v1) search — full revision per item. DO NOT USE in new
        code; v2 uses :meth:`search_deployments`.
        """
        result = await self._deployment_repository.search_legacy_endpoints(action.querier)
        deployments = [_convert_deployment_info_to_legacy_data(info) for info in result.items]
        return SearchLegacyDeploymentsActionResult(
            data=deployments,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def search_deployments_in_project(
        self, action: SearchDeploymentsInProjectAction
    ) -> SearchDeploymentsInProjectActionResult:
        """Search deployments within a project scope."""
        result = await self._deployment_repository.search_deployments_in_project(
            action.querier, action.scope
        )
        return SearchDeploymentsInProjectActionResult(
            data=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def get_deployment_by_id(
        self, action: GetDeploymentByIdAction
    ) -> GetDeploymentByIdActionResult:
        """Get a deployment by ID.

        Args:
            action: Action containing the deployment ID

        Returns:
            GetDeploymentByIdActionResult: Result containing the deployment data

        Raises:
            EndpointNotFound: If the deployment does not exist
        """
        deployment_info = await self._deployment_repository.get_endpoint_info(action.deployment_id)
        return GetDeploymentByIdActionResult(data=_convert_deployment_info_to_data(deployment_info))

    async def get_legacy_deployment_by_id(
        self, action: GetLegacyDeploymentByIdAction
    ) -> GetLegacyDeploymentByIdActionResult:
        """Legacy (REST v1) get-by-id — full revision. DO NOT USE in new code;
        v2 uses :meth:`get_deployment_by_id`.
        """
        deployment_info = await self._deployment_repository.get_legacy_endpoint_info(
            action.deployment_id
        )
        return GetLegacyDeploymentByIdActionResult(
            data=_convert_deployment_info_to_legacy_data(deployment_info)
        )

    async def get_deployment_policy(
        self, action: GetDeploymentPolicyAction
    ) -> GetDeploymentPolicyActionResult:
        """Get the deployment policy for an endpoint.

        Args:
            action: Action containing the endpoint ID

        Returns:
            GetDeploymentPolicyActionResult: Result containing the policy data

        Raises:
            DeploymentPolicyNotFound: If the policy does not exist
        """
        data = await self._deployment_repository.get_deployment_policy(action.deployment_id)
        return GetDeploymentPolicyActionResult(data=data)

    async def search_deployment_policies(
        self, action: SearchDeploymentPoliciesAction
    ) -> SearchDeploymentPoliciesActionResult:
        """Search deployment policies with pagination and ordering."""
        result = await self._deployment_repository.search_deployment_policies(action.querier)
        return SearchDeploymentPoliciesActionResult(
            data=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def upsert_deployment_policy(
        self, action: UpsertDeploymentPolicyAction
    ) -> UpsertDeploymentPolicyActionResult:
        """Create or update a deployment policy using ON CONFLICT."""
        policy_upserter = action.upserter
        spec = DeploymentPolicyUpserterSpec(
            deployment_id=DeploymentID(policy_upserter.deployment_id),
            strategy=policy_upserter.strategy,
            strategy_spec=policy_upserter.strategy_spec,
        )
        repo_upserter: Upserter[DeploymentPolicyRow] = Upserter(spec=spec)
        result = await self._deployment_repository.upsert_deployment_policy(repo_upserter)
        return UpsertDeploymentPolicyActionResult(data=result.data, created=result.created)

    # ========== Revision Operations ==========

    async def add_model_revision(
        self, action: AddModelRevisionAction
    ) -> AddModelRevisionActionResult:
        """Add a new model revision to an existing deployment.

        Delegates to ``DeploymentController.add_deployment_revision()`` which
        owns the full pipeline (preset → base → config/yaml → request merge →
        RBAC-checked revision create → history pruning), and optionally
        activates the new revision based on ``action.auto_activate``.
        """
        revision_data = await self._deployment_controller.add_deployment_revision(
            deployment_id=DeploymentID(action.model_deployment_id),
            revision=action.adder,
            auto_activate=action.auto_activate,
        )
        return AddModelRevisionActionResult(revision=revision_data)

    async def get_revision_by_id(
        self, action: GetRevisionByIdAction
    ) -> GetRevisionByIdActionResult:
        revision = await self._deployment_repository.get_revision(action.revision_id)
        return GetRevisionByIdActionResult(data=revision)

    async def search_revisions(self, action: SearchRevisionsAction) -> SearchRevisionsActionResult:
        """Search revisions with filtering and pagination.

        Args:
            action: Action containing BatchQuerier for filtering and pagination

        Returns:
            SearchRevisionsActionResult: Result containing list of revisions and pagination info
        """
        result = await self._deployment_repository.search_revisions(action.querier)
        return SearchRevisionsActionResult(
            data=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def activate_revision(
        self, action: ActivateRevisionAction
    ) -> ActivateRevisionActionResult:
        """Activate a specific revision by initiating the deployment strategy.

        Delegates to DeploymentController.activate_revision() which validates
        state, sets deploying_revision atomically, and triggers the DEPLOYING
        lifecycle for strategy execution.
        """
        result = await self._deployment_controller.activate_revision(
            action.deployment_id, action.revision_id
        )
        return ActivateRevisionActionResult(
            deployment=_convert_deployment_info_to_data(result.deployment_info),
            previous_revision_id=result.previous_revision_id,
            activated_revision_id=result.activated_revision_id,
            deployment_policy=result.deployment_policy,
        )

    async def admin_refresh_deployment_revisions(
        self, action: RefreshDeploymentRevisionsAction
    ) -> RefreshDeploymentRevisionsActionResult:
        """Refresh revisions for all active deployments.

        For each active deployment, rebuilds a ``ModelRevisionCreator`` from the
        current revision and delegates to
        ``DeploymentController.add_deployment_revision(auto_activate=True)``
        (which re-resolves preset / deployment-config / model_definition and
        activates the new revision). Each deployment is processed independently
        so a single failure does not abort the rest (partial success by design).
        """
        # Bulk scan + independent per-deployment orchestration: multiple repo
        # and controller calls are required by design to preserve partial
        # success semantics. Each inner call owns its own transaction boundary.
        active_querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[
                DeploymentConditions.by_lifecycle_stages(EndpointLifecycle.active_states()),
            ],
        )
        deployment_ids = await self._deployment_repository.search_deployment_ids(
            querier=active_querier,
        )
        results: list[RevisionRefreshResult] = []
        succeeded = 0
        failed = 0
        for deployment_id in deployment_ids:
            try:
                data = await self._deployment_repository.get_current_revision(deployment_id)
                creator = _build_creator_from_revision_data(data)
                new_revision = await self._deployment_controller.add_deployment_revision(
                    deployment_id=deployment_id,
                    revision=creator,
                    auto_activate=True,
                )
                results.append(
                    RevisionRefreshResult(
                        deployment_id=deployment_id,
                        new_revision_id=new_revision.id,
                        success=True,
                        failure_reason=None,
                    )
                )
                succeeded += 1
            except Exception as exc:
                log.warning(
                    "admin_refresh_deployment_revisions failed for deployment {}: {}: {}",
                    deployment_id,
                    type(exc).__name__,
                    exc,
                )
                results.append(
                    RevisionRefreshResult(
                        deployment_id=deployment_id,
                        new_revision_id=None,
                        success=False,
                        failure_reason=f"{type(exc).__name__}: {exc}",
                    )
                )
                failed += 1
        log.info(
            "admin_refresh_deployment_revisions summary: total={} succeeded={} failed={}",
            len(deployment_ids),
            succeeded,
            failed,
        )
        return RefreshDeploymentRevisionsActionResult(results=results)

    # ========== Route Operations ==========

    async def sync_replicas(self, action: SyncReplicaAction) -> SyncReplicaActionResult:
        """Sync replicas for a deployment.

        This triggers a lifecycle check to reconcile the actual replica count
        with the desired replica count based on the current revision.

        Args:
            action: Action containing the deployment ID

        Returns:
            SyncReplicaActionResult: Result indicating success
        """
        # Trigger lifecycle check to sync replicas
        await self._deployment_controller.mark_lifecycle_needed(
            DeploymentLifecycleType.CHECK_REPLICA
        )

        log.info("Triggered replica sync for deployment {}", action.deployment_id)

        return SyncReplicaActionResult(success=True)

    async def search_routes(self, action: SearchRoutesAction) -> SearchRoutesActionResult:
        """Search routes with filtering and pagination.

        Args:
            action: Action containing BatchQuerier for filtering and pagination

        Returns:
            SearchRoutesActionResult: Result containing list of routes and pagination info
        """
        result = await self._deployment_repository.search_routes(action.querier)
        return SearchRoutesActionResult(
            routes=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def search_revision_resource_slots(
        self, action: SearchRevisionResourceSlotsAction
    ) -> SearchRevisionResourceSlotsActionResult:
        """Search resource slots allocated to a deployment revision."""
        (
            items,
            total_count,
            has_next_page,
            has_previous_page,
        ) = await self._deployment_repository.search_revision_resource_slots(
            action.revision_id, action.querier
        )
        return SearchRevisionResourceSlotsActionResult(
            items=items,
            total_count=total_count,
            has_next_page=has_next_page,
            has_previous_page=has_previous_page,
        )

    async def update_route_traffic_status(
        self, action: UpdateRouteTrafficStatusAction
    ) -> UpdateRouteTrafficStatusActionResult:
        """Update route traffic status.

        Args:
            action: Action containing route ID and new traffic status

        Returns:
            UpdateRouteTrafficStatusActionResult: Result containing updated route

        Raises:
            RouteNotFound: If the route does not exist
        """
        route = await self._deployment_controller.update_route_traffic_status(
            route_id=action.route_id,
            traffic_status=action.traffic_status,
        )
        if route is None:
            raise RoutingNotFound
        return UpdateRouteTrafficStatusActionResult(route=route)

    # ========== Auto-scaling Rules ==========

    async def create_auto_scaling_rule(
        self, action: CreateAutoScalingRuleAction
    ) -> CreateAutoScalingRuleActionResult:
        """Create a new auto-scaling rule for a deployment.

        Args:
            action: Action containing the rule creator specification

        Returns:
            CreateAutoScalingRuleActionResult: Result containing the created rule data
        """
        data = await self._deployment_repository.create_model_deployment_autoscaling_rule(
            action.creator
        )
        return CreateAutoScalingRuleActionResult(data=data)

    async def get_auto_scaling_rule(
        self, action: GetAutoScalingRuleAction
    ) -> GetAutoScalingRuleActionResult:
        """Get an auto-scaling rule by ID.

        Args:
            action: Action containing the rule ID

        Returns:
            GetAutoScalingRuleActionResult: Result containing the rule data
        """
        data = await self._deployment_repository.get_model_deployment_autoscaling_rule(
            action.auto_scaling_rule_id
        )
        return GetAutoScalingRuleActionResult(data=data)

    async def update_auto_scaling_rule(
        self, action: UpdateAutoScalingRuleAction
    ) -> UpdateAutoScalingRuleActionResult:
        """Update an existing auto-scaling rule.

        Args:
            action: Action containing the rule ID and modifier

        Returns:
            UpdateAutoScalingRuleActionResult: Result containing the updated rule data
        """
        data = await self._deployment_repository.update_model_deployment_autoscaling_rule(
            action.auto_scaling_rule_id,
            action.modifier,
        )
        return UpdateAutoScalingRuleActionResult(data=data)

    async def delete_auto_scaling_rule(
        self, action: DeleteAutoScalingRuleAction
    ) -> DeleteAutoScalingRuleActionResult:
        """Delete an auto-scaling rule.

        Args:
            action: Action containing the rule ID to delete

        Returns:
            DeleteAutoScalingRuleActionResult: Result indicating success
        """
        success = await self._deployment_repository.delete_autoscaling_rule(
            action.auto_scaling_rule_id
        )
        return DeleteAutoScalingRuleActionResult(success=success)

    async def bulk_delete_auto_scaling_rules(
        self, action: BulkDeleteAutoScalingRulesAction
    ) -> BulkDeleteAutoScalingRulesActionResult:
        """Bulk delete auto-scaling rules."""
        deleted_ids = await self._deployment_repository.bulk_delete_autoscaling_rules(
            action.auto_scaling_rule_ids
        )
        return BulkDeleteAutoScalingRulesActionResult(deleted_ids=deleted_ids)

    # ========== Access Token ==========

    async def _mint_endpoint_jwt(
        self,
        *,
        deployment_id: UUID,
        resource_group: str,
        user_uuid: UUID,
        expires_at: datetime,
    ) -> str:
        """Ask the deployment's app-proxy coordinator to mint an inference JWT.

        Resolves the coordinator behind the deployment's scaling group and
        delegates to :class:`AppProxyClient`. Raises
        :class:`InvalidAPIParameters` when the scaling group has no proxy
        target configured — an opaque local fallback would not pass the
        worker's HS256 check, so refusing here is the only safe option.
        """
        proxy_targets = await self._deployment_repository.fetch_scaling_group_proxy_targets({
            resource_group
        })
        proxy_target = proxy_targets.get(resource_group)
        if proxy_target is None:
            raise InvalidAPIParameters(
                f"No app-proxy target configured for scaling group {resource_group!r}; "
                "cannot issue a deployment access token."
            )

        client = self._appproxy_client_pool.load_client(proxy_target.addr, proxy_target.api_token)
        response = await client.mint_endpoint_token(
            endpoint_id=deployment_id,
            body=MintEndpointTokenRequest(user_uuid=user_uuid, exp=expires_at),
        )
        return response.token

    async def create_access_token(
        self, action: CreateAccessTokenAction
    ) -> CreateAccessTokenActionResult:
        """Create a new access token for a model deployment.

        The token returned to the caller is a JWT issued by the app-proxy
        coordinator (signed with the coordinator's ``jwt_secret``). The
        inference frontend in the worker validates this JWT against the
        circuit id, so a randomly generated opaque token would always be
        rejected with 401.

        Args:
            action: CreateAccessTokenAction containing the creator spec.

        Returns:
            CreateAccessTokenActionResult with the created token data.
        """
        # Get endpoint info to retrieve domain, project, session_owner, resource_group
        endpoint_info = await self._deployment_repository.get_endpoint_info(
            action.creator.model_deployment_id
        )

        expires_at = action.creator.expires_at
        jwt_token = await self._mint_endpoint_jwt(
            deployment_id=action.creator.model_deployment_id,
            resource_group=endpoint_info.metadata.resource_group,
            user_uuid=endpoint_info.metadata.session_owner,
            expires_at=expires_at,
        )

        # Create the RBACEntityCreator with the JWT-bearing spec
        deployment_id = DeploymentID(action.creator.model_deployment_id)
        spec = EndpointTokenCreatorSpec(
            deployment_id=deployment_id,
            domain=endpoint_info.metadata.domain,
            project_id=endpoint_info.metadata.project,
            session_owner_id=endpoint_info.metadata.session_owner,
            expires_at=expires_at,
            token=jwt_token,
        )
        creator: RBACEntityCreator[EndpointTokenRow] = RBACEntityCreator(
            spec=spec,
            element_type=RBACElementType.DEPLOYMENT_TOKEN,
            scope_ref=RBACElementRef(
                element_type=RBACElementType.MODEL_DEPLOYMENT,
                element_id=str(deployment_id),
            ),
        )

        # Create the token via repository
        token_row = await self._deployment_repository.create_access_token(creator)

        data = ModelDeploymentAccessTokenData(
            id=token_row.id,
            token=token_row.token,
            expires_at=token_row.expires_at,
            created_at=token_row.created_at or datetime.now(UTC),
        )
        return CreateAccessTokenActionResult(data=data)

    async def get_access_token(self, action: GetAccessTokenAction) -> GetAccessTokenActionResult:
        """Get an access token by ID."""
        data = await self._deployment_repository.get_access_token(action.access_token_id)
        return GetAccessTokenActionResult(data=data)

    async def delete_access_token(
        self, action: DeleteAccessTokenAction
    ) -> DeleteAccessTokenActionResult:
        """Delete an access token."""
        success = await self._deployment_repository.delete_access_token(action.access_token_id)
        return DeleteAccessTokenActionResult(success=success)

    async def bulk_delete_access_tokens(
        self, action: BulkDeleteAccessTokensAction
    ) -> BulkDeleteAccessTokensActionResult:
        """Bulk delete access tokens."""
        deleted_ids = await self._deployment_repository.bulk_delete_access_tokens(
            action.access_token_ids
        )
        return BulkDeleteAccessTokensActionResult(deleted_ids=deleted_ids)

    # ========== Replica Operations ==========

    async def get_replica_by_id(self, action: GetReplicaByIdAction) -> GetReplicaByIdActionResult:
        """Get a replica by ID."""
        route = await self._deployment_repository.get_route(action.replica_id)
        if route is None:
            return GetReplicaByIdActionResult(data=None)
        return GetReplicaByIdActionResult(data=_convert_route_info_to_replica_data(route))

    # ========== Search Operations ==========

    async def search_replicas(self, action: SearchReplicasAction) -> SearchReplicasActionResult:
        """Search replicas with pagination, ordering, and filtering."""
        result = await self._deployment_repository.search_routes(action.querier)
        replicas = [_convert_route_info_to_replica_data(route) for route in result.items]
        return SearchReplicasActionResult(
            data=replicas,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def search_access_tokens(
        self, action: SearchAccessTokensAction
    ) -> SearchAccessTokensActionResult:
        """Search access tokens with pagination and ordering."""
        result = await self._deployment_repository.search_access_tokens(action.querier)
        return SearchAccessTokensActionResult(
            data=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def search_auto_scaling_rules(
        self, action: SearchAutoScalingRulesAction
    ) -> SearchAutoScalingRulesActionResult:
        """Search auto-scaling rules with pagination and ordering."""
        result = await self._deployment_repository.search_auto_scaling_rules(action.querier)
        return SearchAutoScalingRulesActionResult(
            data=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
