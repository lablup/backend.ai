"""
Mock-based unit tests for DeploymentService CRUD and replica/revision actions.

Tests cover: CreateLegacyDeployment, DestroyDeployment, SyncReplica.
"""

from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.endpoint.types import EndpointLifecycle, ScalingState
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionID
from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.replica_group import ReplicaGroupID
from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.types import ClusterMode, MountPermission, ResourceSlot
from ai.backend.manager.clients.appproxy.client import AppProxyClientPool
from ai.backend.manager.data.deployment.types import (
    ClusterConfigData,
    DeploymentInfo,
    DeploymentMetadata,
    DeploymentNetworkData,
    DeploymentOptions,
    DeploymentState,
    ExecutionData,
    ModelMountConfigData,
    ModelRevisionData,
    ModelRuntimeConfigData,
    PresetAttributionData,
    ReplicaData,
    ResourceConfigData,
)
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.services.deployment.actions.create_legacy_deployment import (
    CreateLegacyDeploymentAction,
)
from ai.backend.manager.services.deployment.actions.destroy_deployment import (
    DestroyDeploymentAction,
)
from ai.backend.manager.services.deployment.actions.sync_replicas import (
    SyncReplicaAction,
)
from ai.backend.manager.services.deployment.service import DeploymentService
from ai.backend.manager.sokovan.deployment import DeploymentController
from ai.backend.manager.sokovan.deployment.types import DeploymentLifecycleType


class DeploymentCRUDBaseFixtures:
    """Shared fixtures for deployment CRUD action tests."""

    @pytest.fixture
    def mock_deployment_repository(self) -> MagicMock:
        return MagicMock(spec=DeploymentRepository)

    @pytest.fixture
    def mock_deployment_controller(self) -> MagicMock:
        return MagicMock(spec=DeploymentController)

    @pytest.fixture
    def mock_appproxy_client_pool(self) -> MagicMock:
        return MagicMock(spec=AppProxyClientPool)

    @pytest.fixture
    def deployment_service(
        self,
        mock_deployment_controller: MagicMock,
        mock_deployment_repository: MagicMock,
        mock_appproxy_client_pool: MagicMock,
    ) -> DeploymentService:
        return DeploymentService(
            deployment_controller=mock_deployment_controller,
            deployment_repository=mock_deployment_repository,
            appproxy_client_pool=mock_appproxy_client_pool,
        )

    @pytest.fixture
    def endpoint_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def deployment_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def endpoint_info(self, endpoint_id: uuid.UUID) -> DeploymentInfo:
        return DeploymentInfo(
            primary_replica_group_id=ReplicaGroupID(uuid.uuid4()),
            id=DeploymentID(endpoint_id),
            metadata=DeploymentMetadata(
                name="test-deployment",
                domain="default",
                project=uuid.uuid4(),
                resource_group="default",
                created_user=uuid.uuid4(),
                session_owner=uuid.uuid4(),
                created_at=datetime(2024, 1, 1, tzinfo=UTC),
                revision_history_limit=10,
            ),
            state=DeploymentState(
                lifecycle=EndpointLifecycle.READY,
                scaling_state=ScalingState.STABLE,
                retry_count=0,
            ),
            replica=ReplicaData(replica_count=2, desired_replica_count=None),
            network=DeploymentNetworkData(
                open_to_public=False, access_token_ids=None, url=None, preferred_domain_name=None
            ),
            options=DeploymentOptions(),
        )

    @pytest.fixture
    def default_querier(self) -> BatchQuerier:
        return BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )


class TestCreateLegacyDeployment(DeploymentCRUDBaseFixtures):
    """Tests for DeploymentService.create_legacy_deployment"""

    @pytest.fixture
    def draft(self, endpoint_info: DeploymentInfo) -> MagicMock:
        """Mock DeploymentCreationDraft."""
        mock_draft = MagicMock()
        mock_draft.name = "test-deployment"
        return mock_draft

    async def test_valid_draft_returns_deployment_info(
        self,
        deployment_service: DeploymentService,
        mock_deployment_repository: MagicMock,
        mock_deployment_controller: MagicMock,
        endpoint_info: DeploymentInfo,
        draft: MagicMock,
    ) -> None:
        """Valid DeploymentCreationDraft returns DeploymentInfo with UUID/metadata/lifecycle."""
        mock_deployment_controller.build_creator_from_legacy_draft = AsyncMock(
            return_value=(MagicMock(), MagicMock())
        )
        mock_deployment_controller.create_deployment = AsyncMock(return_value=endpoint_info)
        mock_deployment_controller.add_deployment_revision = AsyncMock()
        mock_deployment_repository.get_legacy_endpoint_info = AsyncMock(return_value=endpoint_info)

        action = CreateLegacyDeploymentAction(project_id=ProjectID(uuid.uuid4()), draft=draft)
        result = await deployment_service.create_legacy_deployment(action)

        assert result.data == endpoint_info
        assert result.data.id == endpoint_info.id
        assert result.data.metadata.name == "test-deployment"

    async def test_revision_auto_activated(
        self,
        deployment_service: DeploymentService,
        mock_deployment_repository: MagicMock,
        mock_deployment_controller: MagicMock,
        endpoint_info: DeploymentInfo,
        draft: MagicMock,
    ) -> None:
        """Legacy create flow always adds the initial revision with auto_activate=True."""
        mock_deployment_controller.build_creator_from_legacy_draft = AsyncMock(
            return_value=(MagicMock(), MagicMock())
        )
        mock_deployment_controller.create_deployment = AsyncMock(return_value=endpoint_info)
        mock_deployment_controller.add_deployment_revision = AsyncMock()
        mock_deployment_repository.get_legacy_endpoint_info = AsyncMock(return_value=endpoint_info)

        action = CreateLegacyDeploymentAction(project_id=ProjectID(uuid.uuid4()), draft=draft)
        await deployment_service.create_legacy_deployment(action)

        mock_deployment_controller.add_deployment_revision.assert_awaited_once()
        kwargs = mock_deployment_controller.add_deployment_revision.await_args.kwargs
        assert kwargs["deployment_id"] == endpoint_info.id
        assert kwargs["auto_activate"] is True

    @pytest.fixture
    def populated_revision(self) -> ModelRevisionData:
        """A fully-populated revision, as the eager (legacy) getter returns."""
        return ModelRevisionData(
            id=DeploymentRevisionID(uuid.uuid4()),
            deployment_id=DeploymentID(uuid.uuid4()),
            revision_number=1,
            cluster_config=ClusterConfigData(mode=ClusterMode.SINGLE_NODE, size=1),
            resource_config=ResourceConfigData(
                resource_group_name="default",
                resource_slot=ResourceSlot({"cpu": "4", "mem": "8g"}),
            ),
            model_runtime_config=ModelRuntimeConfigData(
                runtime_variant_id=RuntimeVariantID(uuid.uuid4()),
            ),
            model_mount_config=ModelMountConfigData(
                vfolder_id=VFolderUUID(uuid.uuid4()),
                mount_destination="/models",
                definition_path="model-definition.yaml",
                extra_mounts=[],
                model_mount_perm=MountPermission.READ_ONLY,
            ),
            image_id=ImageID(uuid.uuid4()),
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            execution=ExecutionData(startup_command=None, bootstrap_script=None, callback_url=None),
            revision_preset=PresetAttributionData(preset_id=None, values=[]),
        )

    async def test_response_carries_eagerly_loaded_revision(
        self,
        deployment_service: DeploymentService,
        mock_deployment_repository: MagicMock,
        mock_deployment_controller: MagicMock,
        endpoint_info: DeploymentInfo,
        populated_revision: ModelRevisionData,
        draft: MagicMock,
    ) -> None:
        """Regression (#12251): the legacy create response must carry the
        eagerly-loaded revision data so the REST v1 handler can resolve the
        runtime variant. The modern ids-only read path drops
        ``current_revision`` / ``deploying_revision`` (both ``None``), which made
        the handler raise ``RuntimeVariantNotFound`` even though the deployment
        was created. Here the eager (legacy) read returns a populated
        ``deploying_revision`` while the modern read would return ``None``; the
        result must expose the revision regardless of which getter is wired.
        """
        eager_info = replace(endpoint_info, deploying_revision=populated_revision)
        mock_deployment_controller.build_creator_from_legacy_draft = AsyncMock(
            return_value=(MagicMock(), MagicMock())
        )
        mock_deployment_controller.create_deployment = AsyncMock(return_value=endpoint_info)
        mock_deployment_controller.add_deployment_revision = AsyncMock()
        # Eager getter carries the revision; modern getter would drop it (None).
        mock_deployment_repository.get_legacy_endpoint_info = AsyncMock(return_value=eager_info)
        mock_deployment_repository.get_endpoint_info = AsyncMock(return_value=endpoint_info)

        action = CreateLegacyDeploymentAction(project_id=ProjectID(uuid.uuid4()), draft=draft)
        result = await deployment_service.create_legacy_deployment(action)

        # The target revision (current or deploying) the REST v1 handler reads
        # must be present — this is what fails when the modern getter is used.
        target_revision = result.data.current_revision or result.data.deploying_revision
        assert target_revision is not None
        assert (
            target_revision.model_runtime_config.runtime_variant_id
            == populated_revision.model_runtime_config.runtime_variant_id
        )

    async def test_non_existent_domain_raises(
        self,
        deployment_service: DeploymentService,
        mock_deployment_controller: MagicMock,
        draft: MagicMock,
    ) -> None:
        """Non-existent domain raises repository error."""
        mock_deployment_controller.build_creator_from_legacy_draft = AsyncMock(
            side_effect=Exception("Domain not found")
        )

        action = CreateLegacyDeploymentAction(project_id=ProjectID(uuid.uuid4()), draft=draft)
        with pytest.raises(Exception, match="Domain not found"):
            await deployment_service.create_legacy_deployment(action)


class TestDestroyDeployment(DeploymentCRUDBaseFixtures):
    """Tests for DeploymentService.destroy_deployment"""

    async def test_existing_endpoint_returns_success(
        self,
        deployment_service: DeploymentService,
        mock_deployment_repository: MagicMock,
        mock_deployment_controller: MagicMock,
        endpoint_info: DeploymentInfo,
        endpoint_id: uuid.UUID,
    ) -> None:
        """Existing endpoint_id returns success=true with DESTROYING marking."""
        mock_deployment_repository.get_endpoint_info = AsyncMock(return_value=endpoint_info)
        mock_deployment_controller.destroy_deployment = AsyncMock(return_value=True)
        mock_deployment_controller.mark_lifecycle_needed = AsyncMock()

        action = DestroyDeploymentAction(deployment_id=DeploymentID(endpoint_id))
        result = await deployment_service.destroy_deployment(action)

        assert result.success is True
        mock_deployment_controller.mark_lifecycle_needed.assert_called_once_with(
            DeploymentLifecycleType.DESTROYING
        )

    async def test_non_existent_endpoint_raises(
        self,
        deployment_service: DeploymentService,
        mock_deployment_repository: MagicMock,
        mock_deployment_controller: MagicMock,
    ) -> None:
        """Non-existent endpoint raises EndpointNotFound."""
        mock_deployment_repository.get_endpoint_info = AsyncMock(
            side_effect=Exception("EndpointNotFound")
        )

        action = DestroyDeploymentAction(deployment_id=DeploymentID(uuid.uuid4()))
        with pytest.raises(Exception, match="EndpointNotFound"):
            await deployment_service.destroy_deployment(action)

    async def test_already_destroying_handled_idempotently(
        self,
        deployment_service: DeploymentService,
        mock_deployment_repository: MagicMock,
        mock_deployment_controller: MagicMock,
        endpoint_info: DeploymentInfo,
        endpoint_id: uuid.UUID,
    ) -> None:
        """Already DESTROYING state handled idempotently."""
        mock_deployment_repository.get_endpoint_info = AsyncMock(return_value=endpoint_info)
        mock_deployment_controller.destroy_deployment = AsyncMock(return_value=True)
        mock_deployment_controller.mark_lifecycle_needed = AsyncMock()

        action = DestroyDeploymentAction(deployment_id=DeploymentID(endpoint_id))
        result = await deployment_service.destroy_deployment(action)

        assert result.success is True
        mock_deployment_controller.destroy_deployment.assert_called_once_with(endpoint_id)


class TestSyncReplica(DeploymentCRUDBaseFixtures):
    """Tests for DeploymentService.sync_replicas"""

    async def test_triggers_check_replica_marking(
        self,
        deployment_service: DeploymentService,
        mock_deployment_controller: MagicMock,
        deployment_id: uuid.UUID,
    ) -> None:
        """Replica count mismatch triggers CHECK_REPLICA marking."""
        mock_deployment_controller.mark_lifecycle_needed = AsyncMock()

        action = SyncReplicaAction(deployment_id=DeploymentID(deployment_id))
        result = await deployment_service.sync_replicas(action)

        assert result.success is True
        mock_deployment_controller.mark_lifecycle_needed.assert_called_once_with(
            DeploymentLifecycleType.CHECK_REPLICA
        )

    async def test_already_synced_still_marks(
        self,
        deployment_service: DeploymentService,
        mock_deployment_controller: MagicMock,
        deployment_id: uuid.UUID,
    ) -> None:
        """Already synced state still performs marking."""
        mock_deployment_controller.mark_lifecycle_needed = AsyncMock()

        action = SyncReplicaAction(deployment_id=DeploymentID(deployment_id))
        result = await deployment_service.sync_replicas(action)

        assert result.success is True
        mock_deployment_controller.mark_lifecycle_needed.assert_called_once_with(
            DeploymentLifecycleType.CHECK_REPLICA
        )
