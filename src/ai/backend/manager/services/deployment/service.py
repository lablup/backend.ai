"""Deployment service for managing model deployments."""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from ai.backend.common.data.model_deployment.types import (
    DeploymentStrategy,
    ModelDeploymentStatus,
)
from ai.backend.common.types import (
    AutoScalingMetricSource,
    ClusterMode,
    ResourceSlot,
    RuntimeVariant,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    ClusterConfigData,
    DeploymentNetworkSpec,
    ExtraVFolderMountData,
    ModelDeploymentAccessTokenData,
    ModelDeploymentAutoScalingRuleData,
    ModelDeploymentData,
    ModelDeploymentMetadataInfo,
    ModelMountConfigData,
    ModelRevisionData,
    ModelRuntimeConfigData,
    ReplicaStateData,
    ResourceConfigData,
)
from ai.backend.manager.services.deployment.actions.access_token.batch_load import (
    BatchLoadAccessTokensAction,
    BatchLoadAccessTokensActionResult,
)
from ai.backend.manager.services.deployment.actions.access_token.create_access_token import (
    CreateAccessTokenAction,
    CreateAccessTokenActionResult,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.batch_load_auto_scaling_rules import (
    BatchLoadAutoScalingRulesAction,
    BatchLoadAutoScalingRulesActionResult,
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
from ai.backend.manager.services.deployment.actions.batch_load_deployments import (
    BatchLoadDeploymentsAction,
    BatchLoadDeploymentsActionResult,
)
from ai.backend.manager.services.deployment.actions.batch_load_replicas_by_deployment_ids import (
    BatchLoadReplicasByDeploymentIdsAction,
    BatchLoadReplicasByDeploymentIdsActionResult,
)
from ai.backend.manager.services.deployment.actions.batch_load_replicas_by_revision_ids import (
    BatchLoadReplicasByRevisionIdsAction,
    BatchLoadReplicasByRevisionIdsActionResult,
)
from ai.backend.manager.services.deployment.actions.create_deployment import (
    CreateDeploymentAction,
    CreateDeploymentActionResult,
)
from ai.backend.manager.services.deployment.actions.create_legacy_deployment import (
    CreateLegacyDeploymentAction,
    CreateLegacyDeploymentActionResult,
)
from ai.backend.manager.services.deployment.actions.destroy_deployment import (
    DestroyDeploymentAction,
    DestroyDeploymentActionResult,
)
from ai.backend.manager.services.deployment.actions.list_replicas import (
    ListReplicasAction,
    ListReplicasActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.add_model_revision import (
    AddModelRevisionAction,
    AddModelRevisionActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.batch_load_revisions import (
    BatchLoadRevisionsAction,
    BatchLoadRevisionsActionResult,
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
from ai.backend.manager.services.deployment.actions.model_revision.list_revisions import (
    ListRevisionsAction,
    ListRevisionsActionResult,
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


class DeploymentService:
    """Service for managing deployments."""

    _deployment_controller: DeploymentController

    def __init__(self, deployment_controller: DeploymentController) -> None:
        """Initialize deployment service with controller."""
        self._deployment_controller = deployment_controller

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
        log.info("Creating deployment with name: {}", action.creator.name)
        deployment_info = await self._deployment_controller.create_deployment(action.creator)
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

    async def batch_load_deployments(
        self, action: BatchLoadDeploymentsAction
    ) -> BatchLoadDeploymentsActionResult:
        return BatchLoadDeploymentsActionResult(
            data=[
                ModelDeploymentData(
                    id=deployment_id,
                    metadata=ModelDeploymentMetadataInfo(
                        name=f"test-deployment-{i}",
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
                for i, deployment_id in enumerate(action.deployment_ids)
            ]
        )

    async def create_auto_scaling_rule(
        self, action: CreateAutoScalingRuleAction
    ) -> CreateAutoScalingRuleActionResult:
        return CreateAutoScalingRuleActionResult(
            data=ModelDeploymentAutoScalingRuleData(
                id=uuid4(),
                model_deployment_id=action.creator.model_deployment_id,
                metric_source=action.creator.metric_source,
                metric_name=action.creator.metric_name,
                min_threshold=action.creator.min_threshold,
                max_threshold=action.creator.max_threshold,
                step_size=action.creator.step_size,
                time_window=action.creator.time_window,
                min_replicas=action.creator.min_replicas,
                max_replicas=action.creator.max_replicas,
                created_at=datetime.now(),
                last_triggered_at=datetime.now(),
            )
        )

    async def update_auto_scaling_rule(
        self, action: UpdateAutoScalingRuleAction
    ) -> UpdateAutoScalingRuleActionResult:
        return UpdateAutoScalingRuleActionResult(
            data=ModelDeploymentAutoScalingRuleData(
                id=uuid4(),
                model_deployment_id=uuid4(),
                metric_source=AutoScalingMetricSource.KERNEL,
                metric_name="test-metric",
                min_threshold=Decimal("0.5"),
                max_threshold=Decimal("21.0"),
                step_size=1,
                time_window=60,
                min_replicas=1,
                max_replicas=10,
                created_at=datetime.now(),
                last_triggered_at=datetime.now(),
            )
        )

    async def delete_auto_scaling_rule(
        self, action: DeleteAutoScalingRuleAction
    ) -> DeleteAutoScalingRuleActionResult:
        return DeleteAutoScalingRuleActionResult(success=True)

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

    async def batch_load_access_tokens(
        self, action: BatchLoadAccessTokensAction
    ) -> BatchLoadAccessTokensActionResult:
        tokens = []
        for i in range(5):
            tokens.append(
                ModelDeploymentAccessTokenData(
                    id=uuid4(),
                    token=f"test_token_{i}",
                    valid_until=datetime.now() + timedelta(hours=24 * (i + 1)),
                    created_at=datetime.now() - timedelta(hours=i),
                )
            )
        return BatchLoadAccessTokensActionResult(data=tokens)

    async def sync_replicas(self, action: SyncReplicaAction) -> SyncReplicaActionResult:
        return SyncReplicaActionResult(success=True)

    async def add_model_revision(
        self, action: AddModelRevisionAction
    ) -> AddModelRevisionActionResult:
        return AddModelRevisionActionResult(revision=mock_revision_data_2)

    async def batch_load_auto_scaling_rules(
        self, action: BatchLoadAutoScalingRulesAction
    ) -> BatchLoadAutoScalingRulesActionResult:
        return BatchLoadAutoScalingRulesActionResult(
            data=[
                ModelDeploymentAutoScalingRuleData(
                    id=uuid4(),
                    model_deployment_id=uuid4(),
                    metric_source=AutoScalingMetricSource.KERNEL,
                    metric_name="test-metric",
                    min_threshold=Decimal("0.5"),
                    max_threshold=Decimal("21.0"),
                    step_size=1,
                    time_window=60,
                    min_replicas=1,
                    max_replicas=10,
                    created_at=datetime.now(),
                    last_triggered_at=datetime.now(),
                ),
                ModelDeploymentAutoScalingRuleData(
                    id=uuid4(),
                    model_deployment_id=uuid4(),
                    metric_source=AutoScalingMetricSource.KERNEL,
                    metric_name="test-metric",
                    min_threshold=Decimal("0.0"),
                    max_threshold=Decimal("10.0"),
                    step_size=2,
                    time_window=200,
                    min_replicas=1,
                    max_replicas=5,
                    created_at=datetime.now(),
                    last_triggered_at=datetime.now(),
                ),
            ]
        )

    async def list_replicas(self, action: ListReplicasAction) -> ListReplicasActionResult:
        return ListReplicasActionResult(
            data=[],
            total_count=0,
        )

    async def batch_load_revisions(
        self, action: BatchLoadRevisionsAction
    ) -> BatchLoadRevisionsActionResult:
        return BatchLoadRevisionsActionResult(data=[mock_revision_data_1, mock_revision_data_2])

    async def list_revisions(self, action: ListRevisionsAction) -> ListRevisionsActionResult:
        return ListRevisionsActionResult(data=[], total_count=0)

    async def batch_load_replicas_by_deployment_ids(
        self, action: BatchLoadReplicasByDeploymentIdsAction
    ) -> BatchLoadReplicasByDeploymentIdsActionResult:
        return BatchLoadReplicasByDeploymentIdsActionResult(data={})

    async def get_revision_by_deployment_id(
        self, action: GetRevisionByDeploymentIdAction
    ) -> GetRevisionByDeploymentIdActionResult:
        return GetRevisionByDeploymentIdActionResult(data=mock_revision_data_1)

    async def get_revision_by_id(
        self, action: GetRevisionByIdAction
    ) -> GetRevisionByIdActionResult:
        return GetRevisionByIdActionResult(data=mock_revision_data_1)

    async def get_revision_by_replica_id(
        self, action: GetRevisionByReplicaIdAction
    ) -> GetRevisionByReplicaIdActionResult:
        return GetRevisionByReplicaIdActionResult(data=mock_revision_data_1)

    async def get_revisions_by_deployment_id(
        self, action: GetRevisionsByDeploymentIdAction
    ) -> GetRevisionsByDeploymentIdActionResult:
        # For now, return mock revision data list
        return GetRevisionsByDeploymentIdActionResult(
            data=[mock_revision_data_1, mock_revision_data_2]
        )

    async def batch_load_replicas_by_revision_ids(
        self, action: BatchLoadReplicasByRevisionIdsAction
    ) -> BatchLoadReplicasByRevisionIdsActionResult:
        # For now, return empty replica list
        return BatchLoadReplicasByRevisionIdsActionResult(data={})

    async def create_model_revision(
        self, action: CreateModelRevisionAction
    ) -> CreateModelRevisionActionResult:
        return CreateModelRevisionActionResult(revision=mock_revision_data_2)


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
