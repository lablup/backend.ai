"""Deployment service for managing model deployments."""

import logging
from datetime import datetime

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.model_deployment.types import (
    DeploymentStrategy,
    ModelDeploymentStatus,
)
from ai.backend.common.types import (
    ResourceSlot,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    ActivenessStatus,
    ClusterConfigData,
    DeploymentInfo,
    ExtraVFolderMountData,
    LivenessStatus,
    ModelDeploymentAccessTokenData,
    ModelDeploymentData,
    ModelDeploymentMetadataInfo,
    ModelMountConfigData,
    ModelReplicaData,
    ModelRevisionData,
    ModelRuntimeConfigData,
    ReadinessStatus,
    ReplicaStateData,
    ResourceConfigData,
    RouteInfo,
)
from ai.backend.manager.models.endpoint import EndpointRow, EndpointTokenRow
from ai.backend.manager.repositories.base import Creator
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.repositories.deployment.creators import (
    DeploymentCreatorSpec,
    DeploymentExecutionFields,
    DeploymentMetadataFields,
    DeploymentMountFields,
    DeploymentNetworkFields,
    DeploymentReplicaFields,
    DeploymentResourceFields,
    EndpointTokenCreatorSpec,
    ModelRevisionFields,
)
from ai.backend.manager.services.deployment.actions.access_token.create_access_token import (
    CreateAccessTokenAction,
    CreateAccessTokenActionResult,
)
from ai.backend.manager.services.deployment.actions.access_token.search_access_tokens import (
    SearchAccessTokensAction,
    SearchAccessTokensActionResult,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.create_auto_scaling_rule import (
    CreateAutoScalingRuleAction,
    CreateAutoScalingRuleActionResult,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.delete_auto_scaling_rule import (
    DeleteAutoScalingRuleAction,
    DeleteAutoScalingRuleActionResult,
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
)
from ai.backend.manager.services.deployment.actions.destroy_deployment import (
    DestroyDeploymentAction,
    DestroyDeploymentActionResult,
)
from ai.backend.manager.services.deployment.actions.get_deployment_by_id import (
    GetDeploymentByIdAction,
    GetDeploymentByIdActionResult,
)
from ai.backend.manager.services.deployment.actions.get_replica_by_id import (
    GetReplicaByIdAction,
    GetReplicaByIdActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.add_model_revision import (
    AddModelRevisionAction,
    AddModelRevisionActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.create_model_revision import (
    CreateModelRevisionAction,
    CreateModelRevisionActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.get_revision_by_id import (
    GetRevisionByIdAction,
    GetRevisionByIdActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.search_revisions import (
    SearchRevisionsAction,
    SearchRevisionsActionResult,
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
    """Map EndpointLifecycle to ModelDeploymentStatus."""
    match lifecycle:
        case EndpointLifecycle.PENDING:
            return ModelDeploymentStatus.PENDING
        case EndpointLifecycle.CREATED | EndpointLifecycle.READY:
            return ModelDeploymentStatus.READY
        case EndpointLifecycle.SCALING:
            return ModelDeploymentStatus.SCALING
        case EndpointLifecycle.DEPLOYING:
            return ModelDeploymentStatus.DEPLOYING
        case EndpointLifecycle.DESTROYING:
            return ModelDeploymentStatus.STOPPING
        case EndpointLifecycle.DESTROYED:
            return ModelDeploymentStatus.STOPPED
        case _:
            return ModelDeploymentStatus.PENDING


def _convert_deployment_info_to_data(info: DeploymentInfo) -> ModelDeploymentData:
    """Convert DeploymentInfo to ModelDeploymentData.

    Note: Some fields are set to defaults as DeploymentInfo doesn't have all the data.
    """
    # Map revision if available
    revision: ModelRevisionData | None = None
    if info.model_revisions:
        rev = info.model_revisions[0]
        revision = ModelRevisionData(
            id=info.current_revision_id or info.id,
            name=rev.image_identifier.canonical,
            cluster_config=ClusterConfigData(
                mode=rev.resource_spec.cluster_mode,
                size=rev.resource_spec.cluster_size,
            ),
            resource_config=ResourceConfigData(
                resource_group_name=info.metadata.resource_group,
                resource_slot=ResourceSlot.from_json(rev.resource_spec.resource_slots),
            ),
            model_mount_config=ModelMountConfigData(
                vfolder_id=rev.mounts.model_vfolder_id,
                mount_destination=rev.mounts.model_mount_destination,
                definition_path=rev.mounts.model_definition_path or "",
            ),
            model_runtime_config=ModelRuntimeConfigData(
                runtime_variant=rev.execution.runtime_variant,
                inference_runtime_config=rev.execution.inference_runtime_config or {},
            ),
            extra_vfolder_mounts=[
                ExtraVFolderMountData(
                    vfolder_id=m.vfid.folder_id,
                    mount_destination=m.kernel_path.as_posix(),
                )
                for m in rev.mounts.extra_mounts
            ],
            image_id=info.current_revision_id
            or info.id,  # Placeholder: actual image_id not in ImageIdentifier
            created_at=info.metadata.created_at or datetime.now(),
        )

    desired_count = info.replica_spec.desired_replica_count
    if desired_count is None:
        desired_count = info.replica_spec.replica_count

    return ModelDeploymentData(
        id=info.id,
        metadata=ModelDeploymentMetadataInfo(
            name=info.metadata.name,
            status=_map_lifecycle_to_status(info.state.lifecycle),
            tags=[info.metadata.tag] if info.metadata.tag else [],
            project_id=info.metadata.project,
            domain_name=info.metadata.domain,
            created_at=info.metadata.created_at or datetime.now(),
            updated_at=info.metadata.created_at or datetime.now(),
        ),
        network_access=info.network,
        revision_history_ids=[info.current_revision_id] if info.current_revision_id else [],
        revision=revision,
        scaling_rule_ids=[],  # Not available in DeploymentInfo
        replica_state=ReplicaStateData(
            desired_replica_count=desired_count,
            replica_ids=[],  # Not available in DeploymentInfo
        ),
        default_deployment_strategy=DeploymentStrategy.ROLLING,
        created_user_id=info.metadata.created_user,
    )


def _convert_route_info_to_replica_data(route: RouteInfo) -> ModelReplicaData:
    """Convert RouteInfo to ModelReplicaData.

    Note: Some fields are set to defaults as RouteInfo doesn't have all the data.
    """
    return ModelReplicaData(
        id=route.route_id,
        revision_id=route.revision_id
        or route.endpoint_id,  # Fallback to endpoint_id if no revision
        session_id=route.session_id or route.route_id,  # type: ignore[arg-type]  # Fallback if no session
        readiness_status=ReadinessStatus.HEALTHY,  # Derived from route status
        liveness_status=LivenessStatus.HEALTHY,  # Default
        activeness_status=ActivenessStatus.ACTIVE
        if route.traffic_ratio > 0
        else ActivenessStatus.INACTIVE,
        weight=int(route.traffic_ratio * 100),  # Convert ratio to weight
        detail=route.error_data,
        created_at=route.created_at,
        live_stat={},  # Not available in RouteInfo
    )


class DeploymentService:
    """Service for managing deployments."""

    _deployment_controller: DeploymentController
    _deployment_repository: DeploymentRepository

    def __init__(
        self,
        deployment_controller: DeploymentController,
        deployment_repository: DeploymentRepository,
    ) -> None:
        """Initialize deployment service with controller and repository."""
        self._deployment_controller = deployment_controller
        self._deployment_repository = deployment_repository

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

        # Build CreatorSpec from action data
        metadata = action.creator.metadata
        revision = action.creator.model_revision
        mounts = revision.mounts

        creator_spec = DeploymentCreatorSpec(
            metadata=DeploymentMetadataFields(
                name=metadata.name,
                domain=metadata.domain,
                project_id=metadata.project,
                resource_group=metadata.resource_group,
                created_user_id=metadata.created_user,
                session_owner_id=metadata.session_owner,
                revision_history_limit=metadata.revision_history_limit,
                tag=metadata.tag,
            ),
            replica=DeploymentReplicaFields(
                replica_count=action.creator.replica_spec.replica_count,
                desired_replica_count=action.creator.replica_spec.desired_replica_count,
            ),
            network=DeploymentNetworkFields(
                open_to_public=action.creator.network.open_to_public,
                url=action.creator.network.url,
            ),
            revision=ModelRevisionFields(
                image_id=revision.image_id,
                resource=DeploymentResourceFields(
                    cluster_mode=revision.resource_spec.cluster_mode,
                    cluster_size=revision.resource_spec.cluster_size,
                    resource_slots=ResourceSlot(revision.resource_spec.resource_slots),
                    resource_opts=revision.resource_spec.resource_opts,
                ),
                mounts=DeploymentMountFields(
                    model_vfolder_id=mounts.model_vfolder_id,
                    model_mount_destination=mounts.model_mount_destination,
                    model_definition_path=mounts.model_definition_path,
                    extra_mounts=(),  # TODO: Convert MountInfo to VFolderMount
                ),
                execution=DeploymentExecutionFields(
                    runtime_variant=revision.execution.runtime_variant,
                    startup_command=revision.execution.startup_command,
                    bootstrap_script=revision.execution.bootstrap_script,
                    environ=revision.execution.environ,
                    callback_url=revision.execution.callback_url,
                ),
            ),
        )
        creator: Creator[EndpointRow] = Creator(spec=creator_spec)

        # Create endpoint via repository
        deployment_info = await self._deployment_repository.create_endpoint(
            creator, action.creator.policy
        )

        # Mark lifecycle needed to start provisioning
        await self._deployment_controller.mark_lifecycle_needed(
            DeploymentLifecycleType.CHECK_PENDING
        )

        return CreateDeploymentActionResult(data=_convert_deployment_info_to_data(deployment_info))

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
        deployment_info = await self._deployment_controller.create_deployment(action.draft)
        await self._deployment_controller.mark_lifecycle_needed(
            DeploymentLifecycleType.CHECK_PENDING
        )
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

        # Update endpoint and get updated deployment info in one call
        deployment_info = await self._deployment_repository.update_endpoint(action.updater)

        # Mark lifecycle needed for potential replica adjustments
        await self._deployment_controller.mark_lifecycle_needed(
            DeploymentLifecycleType.CHECK_REPLICA
        )

        return UpdateDeploymentActionResult(data=_convert_deployment_info_to_data(deployment_info))

    async def destroy_deployment(
        self, action: DestroyDeploymentAction
    ) -> DestroyDeploymentActionResult:
        """Destroy an existing deployment.

        Args:
            action: Destroy deployment action containing the endpoint ID

        Returns:
            DestroyDeploymentActionResult: Result indicating success or failure
        """
        log.info("Destroying deployment with ID: {}", action.endpoint_id)
        success = await self._deployment_controller.destroy_deployment(action.endpoint_id)
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
        data = await self._deployment_controller.get_deployment_policy(action.endpoint_id)
        return GetDeploymentPolicyActionResult(data=data)

    # ========== Revision Operations ==========

    async def add_model_revision(
        self, action: AddModelRevisionAction
    ) -> AddModelRevisionActionResult:
        # TODO: Implement full revision creation logic
        # This requires integration with the controller's revision generator system:
        # 1. Get default architecture from scaling group
        # 2. Use revision generator to resolve image and build ModelRevisionSpec
        # 3. Get latest revision number via get_latest_revision_number()
        # 4. Build DeploymentRevisionCreatorSpec and create revision
        raise NotImplementedError(
            "add_model_revision requires controller's revision generator for image resolution. "
            "Use create_legacy_deployment for deployment creation with revision."
        )

    async def create_model_revision(
        self, action: CreateModelRevisionAction
    ) -> CreateModelRevisionActionResult:
        # TODO: Implement full revision creation logic
        # Note: CreateModelRevisionAction is missing deployment_id field
        # This requires integration with the controller's revision generator system
        raise NotImplementedError(
            "create_model_revision requires controller's revision generator for image resolution "
            "and is missing deployment_id in action definition."
        )

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
        """Activate a specific revision to be the current revision.

        Args:
            action: Action containing deployment and revision IDs

        Returns:
            ActivateRevisionActionResult: Result containing the updated deployment
        """
        # 1. Validate revision exists (raises exception if not found)
        _revision = await self._deployment_repository.get_revision(action.revision_id)

        # 2. Update endpoint.current_revision and get previous revision
        previous_revision_id = await self._deployment_repository.update_current_revision(
            action.deployment_id, action.revision_id
        )

        # 3. Trigger lifecycle check to update routes with new revision
        await self._deployment_controller.mark_lifecycle_needed(
            DeploymentLifecycleType.CHECK_REPLICA
        )

        log.info(
            "Activated revision {} for deployment {} (previous: {})",
            action.revision_id,
            action.deployment_id,
            previous_revision_id,
        )

        # 4. Get updated deployment info
        deployment_info = await self._deployment_repository.get_endpoint_info(action.deployment_id)

        return ActivateRevisionActionResult(
            deployment=_convert_deployment_info_to_data(deployment_info),
            previous_revision_id=previous_revision_id,
            activated_revision_id=action.revision_id,
        )

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
        from ai.backend.manager.errors.service import RoutingNotFound

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

    # ========== Access Token ==========

    async def create_access_token(
        self, action: CreateAccessTokenAction
    ) -> CreateAccessTokenActionResult:
        """Create a new access token for a model deployment.

        Args:
            action: CreateAccessTokenAction containing the creator spec.

        Returns:
            CreateAccessTokenActionResult with the created token data.
        """
        # Get endpoint info to retrieve domain, project, session_owner
        endpoint_info = await self._deployment_repository.get_endpoint_info(
            action.creator.model_deployment_id
        )

        # Create the Creator with EndpointTokenCreatorSpec
        spec = EndpointTokenCreatorSpec(
            endpoint_id=action.creator.model_deployment_id,
            domain=endpoint_info.metadata.domain,
            project_id=endpoint_info.metadata.project,
            session_owner_id=endpoint_info.metadata.session_owner,
        )
        creator: Creator[EndpointTokenRow] = Creator(spec=spec)

        # Create the token via repository
        token_row = await self._deployment_repository.create_access_token(creator)

        # Convert to ModelDeploymentAccessTokenData
        # Note: valid_until is returned as provided but not persisted in DB
        data = ModelDeploymentAccessTokenData(
            id=token_row.id,
            token=token_row.token,
            valid_until=action.creator.valid_until,
            created_at=token_row.created_at or datetime.now(),
        )
        return CreateAccessTokenActionResult(data=data)

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
