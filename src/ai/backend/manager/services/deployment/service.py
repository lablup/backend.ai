"""Deployment service for managing model deployments."""

import logging
from datetime import datetime, timedelta
from uuid import uuid4

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.model_deployment.types import (
    DeploymentStrategy,
    ModelDeploymentStatus,
)
from ai.backend.common.types import (
    ClusterMode,
    ResourceSlot,
    RuntimeVariant,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    ClusterConfigData,
    DeploymentInfo,
    DeploymentNetworkSpec,
    ExtraVFolderMountData,
    ModelDeploymentAccessTokenData,
    ModelDeploymentData,
    ModelDeploymentMetadataInfo,
    ModelMountConfigData,
    ModelRevisionData,
    ModelRuntimeConfigData,
    ReplicaStateData,
    ResourceConfigData,
)
from ai.backend.manager.repositories.base.pagination import OffsetPagination
from ai.backend.manager.repositories.base.querier import BatchQuerier
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.repositories.deployment.options import RevisionConditions
from ai.backend.manager.services.deployment.actions.access_token.create_access_token import (
    CreateAccessTokenAction,
    CreateAccessTokenActionResult,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.create_auto_scaling_rule import (
    CreateAutoScalingRuleAction,
    CreateAutoScalingRuleActionResult,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.delete_auto_scaling_rule import (
    DeleteAutoScalingRuleAction,
    DeleteAutoScalingRuleActionResult,
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
from ai.backend.manager.services.deployment.actions.model_revision.add_model_revision import (
    AddModelRevisionAction,
    AddModelRevisionActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.create_model_revision import (
    CreateModelRevisionAction,
    CreateModelRevisionActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.get_revision_by_deployment_id import (
    GetRevisionByDeploymentIdAction,
    GetRevisionByDeploymentIdActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.get_revision_by_id import (
    GetRevisionByIdAction,
    GetRevisionByIdActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.get_revision_by_replica_id import (
    GetRevisionByReplicaIdAction,
    GetRevisionByReplicaIdActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.get_revisions_by_deployment_id import (
    GetRevisionsByDeploymentIdAction,
    GetRevisionsByDeploymentIdActionResult,
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
        return CreateDeploymentActionResult(
            data=ModelDeploymentData(
                id=uuid4(),
                metadata=ModelDeploymentMetadataInfo(
                    name="test-deployment",
                    status=ModelDeploymentStatus.READY,
                    tags=["tag1", "tag2"],
                    project_id=uuid4(),
                    domain_name="default",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                ),
                network_access=DeploymentNetworkSpec(
                    open_to_public=True,
                    url="http://example.com",
                    preferred_domain_name="example.com",
                    access_token_ids=[uuid4()],
                ),
                revision_history_ids=[uuid4(), uuid4()],
                revision=mock_revision_data_1,
                scaling_rule_ids=[uuid4(), uuid4()],
                replica_state=ReplicaStateData(
                    desired_replica_count=3,
                    replica_ids=[uuid4(), uuid4(), uuid4()],
                ),
                default_deployment_strategy=DeploymentStrategy.ROLLING,
                created_user_id=uuid4(),
            )
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
        deployment_info = await self._deployment_controller.create_deployment(action.draft)
        await self._deployment_controller.mark_lifecycle_needed(
            DeploymentLifecycleType.CHECK_PENDING
        )
        return CreateLegacyDeploymentActionResult(data=deployment_info)

    async def update_deployment(
        self, action: UpdateDeploymentAction
    ) -> UpdateDeploymentActionResult:
        await self._deployment_controller.mark_lifecycle_needed(
            DeploymentLifecycleType.CHECK_REPLICA
        )
        return UpdateDeploymentActionResult(
            data=ModelDeploymentData(
                id=action.deployment_id,
                metadata=ModelDeploymentMetadataInfo(
                    name="test-deployment",
                    status=ModelDeploymentStatus.READY,
                    tags=["tag1", "tag2"],
                    project_id=uuid4(),
                    domain_name="default",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                ),
                network_access=DeploymentNetworkSpec(
                    open_to_public=True,
                    url="http://example.com",
                    preferred_domain_name="example.com",
                    access_token_ids=[uuid4()],
                ),
                revision_history_ids=[uuid4(), uuid4()],
                revision=mock_revision_data_1,
                scaling_rule_ids=[uuid4(), uuid4()],
                replica_state=ReplicaStateData(
                    desired_replica_count=3,
                    replica_ids=[uuid4(), uuid4(), uuid4()],
                ),
                default_deployment_strategy=DeploymentStrategy.ROLLING,
                created_user_id=uuid4(),
            )
        )

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
            deployments=deployments,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
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
        data = await self._deployment_controller.get_deployment_policy(action.endpoint_id)
        return GetDeploymentPolicyActionResult(data=data)

    # ========== Revision Operations ==========

    async def add_model_revision(
        self, action: AddModelRevisionAction
    ) -> AddModelRevisionActionResult:
        # TODO: Implement full revision creation logic
        # 1. Resolve image ID from action.adder.image_identifier
        # 2. Get latest revision number via get_latest_revision_number(action.model_deployment_id)
        # 3. Build DeploymentRevisionCreatorSpec from action.adder
        # 4. Create revision via repository.create_revision(creator)
        raise NotImplementedError(
            "add_model_revision requires full ModelRevisionCreator to "
            "DeploymentRevisionCreatorSpec conversion - pending implementation"
        )

    async def create_model_revision(
        self, action: CreateModelRevisionAction
    ) -> CreateModelRevisionActionResult:
        # TODO: Implement full revision creation logic
        # 1. Resolve image ID from action.creator.image_identifier
        # 2. Get latest revision number via get_latest_revision_number()
        # 3. Build DeploymentRevisionCreatorSpec from action.creator
        # 4. Create revision via repository.create_revision(creator)
        raise NotImplementedError(
            "create_model_revision requires full ModelRevisionCreator to "
            "DeploymentRevisionCreatorSpec conversion - pending implementation"
        )

    async def get_revision_by_id(
        self, action: GetRevisionByIdAction
    ) -> GetRevisionByIdActionResult:
        revision = await self._deployment_repository.get_revision(action.revision_id)
        return GetRevisionByIdActionResult(data=revision)

    async def get_revision_by_deployment_id(
        self, action: GetRevisionByDeploymentIdAction
    ) -> GetRevisionByDeploymentIdActionResult:
        revision = await self._deployment_repository.get_current_revision(action.deployment_id)
        return GetRevisionByDeploymentIdActionResult(data=revision)

    async def get_revision_by_replica_id(
        self, action: GetRevisionByReplicaIdAction
    ) -> GetRevisionByReplicaIdActionResult:
        revision = await self._deployment_repository.get_revision_by_route_id(action.replica_id)
        return GetRevisionByReplicaIdActionResult(data=revision)

    async def get_revisions_by_deployment_id(
        self, action: GetRevisionsByDeploymentIdAction
    ) -> GetRevisionsByDeploymentIdActionResult:
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[RevisionConditions.by_deployment_id(action.deployment_id)],
        )
        result = await self._deployment_repository.search_revisions(querier)
        return GetRevisionsByDeploymentIdActionResult(data=result.items)

    async def search_revisions(self, action: SearchRevisionsAction) -> SearchRevisionsActionResult:
        """Search revisions with filtering and pagination.

        Args:
            action: Action containing BatchQuerier for filtering and pagination

        Returns:
            SearchRevisionsActionResult: Result containing list of revisions and pagination info
        """
        result = await self._deployment_repository.search_revisions(action.querier)
        return SearchRevisionsActionResult(
            revisions=result.items,
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
        # 1. Validate revision exists
        revision = await self._deployment_repository.get_revision(action.revision_id)

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

        # 4. Return result with activated revision data
        # Note: ModelDeploymentData requires additional data that needs separate implementation
        # For now, we return minimal data with the activated revision
        return ActivateRevisionActionResult(
            deployment=ModelDeploymentData(
                id=action.deployment_id,
                metadata=ModelDeploymentMetadataInfo(
                    name=revision.name or "",
                    status=ModelDeploymentStatus.READY,
                    tags=[],
                    project_id=uuid4(),  # TODO: Get from deployment
                    domain_name="default",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                ),
                network_access=DeploymentNetworkSpec(
                    open_to_public=True,
                    url="",
                ),
                revision_history_ids=[action.revision_id],
                revision=revision,
                scaling_rule_ids=[],
                replica_state=ReplicaStateData(
                    desired_replica_count=0,
                    replica_ids=[],
                ),
                default_deployment_strategy=DeploymentStrategy.ROLLING,
                created_user_id=uuid4(),  # TODO: Get from deployment
            ),
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
        return CreateAccessTokenActionResult(
            data=ModelDeploymentAccessTokenData(
                id=uuid4(),
                token="test_token",
                valid_until=datetime.now() + timedelta(hours=1),
                created_at=datetime.now(),
            )
        )


mock_revision_data_1 = ModelRevisionData(
    id=uuid4(),
    name="test-revision",
    cluster_config=ClusterConfigData(
        mode=ClusterMode.SINGLE_NODE,
        size=1,
    ),
    resource_config=ResourceConfigData(
        resource_group_name="default",
        resource_slot=ResourceSlot.from_json({"cpu": 1, "memory": 1024}),
    ),
    model_mount_config=ModelMountConfigData(
        vfolder_id=uuid4(),
        mount_destination="/model",
        definition_path="model-definition.yaml",
    ),
    model_runtime_config=ModelRuntimeConfigData(
        runtime_variant=RuntimeVariant.VLLM,
        inference_runtime_config={"tp_size": 2, "max_length": 1024},
    ),
    extra_vfolder_mounts=[
        ExtraVFolderMountData(
            vfolder_id=uuid4(),
            mount_destination="/var",
        ),
        ExtraVFolderMountData(
            vfolder_id=uuid4(),
            mount_destination="/example",
        ),
    ],
    image_id=uuid4(),
    created_at=datetime.now(),
)

mock_revision_data_2 = ModelRevisionData(
    id=uuid4(),
    name="test-revision-2",
    cluster_config=ClusterConfigData(
        mode=ClusterMode.MULTI_NODE,
        size=1,
    ),
    resource_config=ResourceConfigData(
        resource_group_name="default",
        resource_slot=ResourceSlot.from_json({"cpu": 1, "memory": 1024}),
    ),
    model_mount_config=ModelMountConfigData(
        vfolder_id=uuid4(),
        mount_destination="/model",
        definition_path="model-definition.yaml",
    ),
    model_runtime_config=ModelRuntimeConfigData(
        runtime_variant=RuntimeVariant.NIM,
        inference_runtime_config={"tp_size": 2, "max_length": 1024},
    ),
    image_id=uuid4(),
    created_at=datetime.now(),
)
