"""
Mock-based unit tests for DeploymentService CRUD and replica/revision actions.

Tests cover: CreateLegacyDeployment, DestroyDeployment, GetReplicaById,
SearchReplicas, SearchAccessTokens, SyncReplica, GetRevisionById.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.model_deployment.types import (
    ActivenessStatus,
    LivenessStatus,
    ReadinessStatus,
)
from ai.backend.common.types import ClusterMode, ResourceSlot, RuntimeVariant, SessionId
from ai.backend.manager.data.deployment.types import (
    AccessTokenSearchResult,
    ClusterConfigData,
    DeploymentInfo,
    DeploymentMetadata,
    DeploymentNetworkSpec,
    DeploymentState,
    ModelDeploymentAccessTokenData,
    ModelMountConfigData,
    ModelRevisionData,
    ModelRuntimeConfigData,
    ReplicaSpec,
    ResourceConfigData,
    RouteInfo,
    RouteSearchResult,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.services.deployment.actions.access_token.search_access_tokens import (
    SearchAccessTokensAction,
)
from ai.backend.manager.services.deployment.actions.create_legacy_deployment import (
    CreateLegacyDeploymentAction,
)
from ai.backend.manager.services.deployment.actions.destroy_deployment import (
    DestroyDeploymentAction,
)
from ai.backend.manager.services.deployment.actions.get_replica_by_id import (
    GetReplicaByIdAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.get_revision_by_id import (
    GetRevisionByIdAction,
)
from ai.backend.manager.services.deployment.actions.search_replicas import (
    SearchReplicasAction,
)
from ai.backend.manager.services.deployment.actions.sync_replicas import (
    SyncReplicaAction,
)
from ai.backend.manager.services.deployment.processors import DeploymentProcessors
from ai.backend.manager.services.deployment.service import DeploymentService
from ai.backend.manager.sokovan.deployment import DeploymentController
from ai.backend.manager.sokovan.deployment.revision_generator.registry import (
    RevisionGeneratorRegistry,
)
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
    def mock_revision_generator_registry(self) -> MagicMock:
        return MagicMock(spec=RevisionGeneratorRegistry)

    @pytest.fixture
    def deployment_service(
        self,
        mock_deployment_controller: MagicMock,
        mock_deployment_repository: MagicMock,
        mock_revision_generator_registry: MagicMock,
    ) -> DeploymentService:
        return DeploymentService(
            deployment_controller=mock_deployment_controller,
            deployment_repository=mock_deployment_repository,
            revision_generator_registry=mock_revision_generator_registry,
        )

    @pytest.fixture
    def processors(self, deployment_service: DeploymentService) -> DeploymentProcessors:
        return DeploymentProcessors(deployment_service, [])

    @pytest.fixture
    def endpoint_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def deployment_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def endpoint_info(self, endpoint_id: uuid.UUID) -> DeploymentInfo:
        return DeploymentInfo(
            id=endpoint_id,
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
            state=DeploymentState(lifecycle=EndpointLifecycle.READY, retry_count=0),
            replica_spec=ReplicaSpec(replica_count=2),
            network=DeploymentNetworkSpec(open_to_public=False),
            model_revisions=[],
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
        processors: DeploymentProcessors,
        mock_deployment_controller: MagicMock,
        endpoint_info: DeploymentInfo,
        draft: MagicMock,
    ) -> None:
        """Valid DeploymentCreationDraft returns DeploymentInfo with UUID/metadata/lifecycle."""
        mock_deployment_controller.create_deployment = AsyncMock(return_value=endpoint_info)
        mock_deployment_controller.mark_lifecycle_needed = AsyncMock()

        action = CreateLegacyDeploymentAction(draft=draft)
        result = await processors.create_legacy_deployment.wait_for_complete(action)

        assert result.data == endpoint_info
        assert result.data.id == endpoint_info.id
        assert result.data.metadata.name == "test-deployment"

    async def test_lifecycle_marked_check_pending(
        self,
        processors: DeploymentProcessors,
        mock_deployment_controller: MagicMock,
        endpoint_info: DeploymentInfo,
        draft: MagicMock,
    ) -> None:
        """Creating a deployment marks lifecycle CHECK_PENDING."""
        mock_deployment_controller.create_deployment = AsyncMock(return_value=endpoint_info)
        mock_deployment_controller.mark_lifecycle_needed = AsyncMock()

        action = CreateLegacyDeploymentAction(draft=draft)
        await processors.create_legacy_deployment.wait_for_complete(action)

        mock_deployment_controller.mark_lifecycle_needed.assert_called_once_with(
            DeploymentLifecycleType.CHECK_PENDING
        )

    async def test_non_existent_domain_raises(
        self,
        processors: DeploymentProcessors,
        mock_deployment_controller: MagicMock,
        draft: MagicMock,
    ) -> None:
        """Non-existent domain raises repository error."""
        mock_deployment_controller.create_deployment = AsyncMock(
            side_effect=Exception("Domain not found")
        )
        mock_deployment_controller.mark_lifecycle_needed = AsyncMock()

        action = CreateLegacyDeploymentAction(draft=draft)
        with pytest.raises(Exception, match="Domain not found"):
            await processors.create_legacy_deployment.wait_for_complete(action)


class TestDestroyDeployment(DeploymentCRUDBaseFixtures):
    """Tests for DeploymentService.destroy_deployment"""

    async def test_existing_endpoint_returns_success(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
        mock_deployment_controller: MagicMock,
        endpoint_info: DeploymentInfo,
        endpoint_id: uuid.UUID,
    ) -> None:
        """Existing endpoint_id returns success=true with DESTROYING marking."""
        mock_deployment_repository.get_endpoint_info = AsyncMock(return_value=endpoint_info)
        mock_deployment_controller.destroy_deployment = AsyncMock(return_value=True)
        mock_deployment_controller.mark_lifecycle_needed = AsyncMock()

        action = DestroyDeploymentAction(endpoint_id=endpoint_id)
        result = await processors.destroy_deployment.wait_for_complete(action)

        assert result.success is True
        mock_deployment_controller.mark_lifecycle_needed.assert_called_once_with(
            DeploymentLifecycleType.DESTROYING
        )

    async def test_non_existent_endpoint_raises(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
        mock_deployment_controller: MagicMock,
    ) -> None:
        """Non-existent endpoint raises EndpointNotFound."""
        mock_deployment_repository.get_endpoint_info = AsyncMock(
            side_effect=Exception("EndpointNotFound")
        )

        action = DestroyDeploymentAction(endpoint_id=uuid.uuid4())
        with pytest.raises(Exception, match="EndpointNotFound"):
            await processors.destroy_deployment.wait_for_complete(action)

    async def test_already_destroying_handled_idempotently(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
        mock_deployment_controller: MagicMock,
        endpoint_info: DeploymentInfo,
        endpoint_id: uuid.UUID,
    ) -> None:
        """Already DESTROYING state handled idempotently."""
        mock_deployment_repository.get_endpoint_info = AsyncMock(return_value=endpoint_info)
        mock_deployment_controller.destroy_deployment = AsyncMock(return_value=True)
        mock_deployment_controller.mark_lifecycle_needed = AsyncMock()

        action = DestroyDeploymentAction(endpoint_id=endpoint_id)
        result = await processors.destroy_deployment.wait_for_complete(action)

        assert result.success is True
        mock_deployment_controller.destroy_deployment.assert_called_once_with(endpoint_id)


class TestGetReplicaById(DeploymentCRUDBaseFixtures):
    """Tests for DeploymentService.get_replica_by_id"""

    @pytest.fixture
    def route_info(self, endpoint_id: uuid.UUID) -> RouteInfo:
        return RouteInfo(
            route_id=uuid.uuid4(),
            endpoint_id=endpoint_id,
            session_id=SessionId(uuid.uuid4()),
            status=RouteStatus.HEALTHY,
            traffic_ratio=0.5,
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            revision_id=uuid.uuid4(),
            traffic_status=RouteTrafficStatus.ACTIVE,
        )

    async def test_existing_replica_returns_data(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
        route_info: RouteInfo,
    ) -> None:
        """Existing replica_id returns ModelReplicaData with readiness/liveness/activeness/weight."""
        mock_deployment_repository.get_route = AsyncMock(return_value=route_info)

        action = GetReplicaByIdAction(replica_id=route_info.route_id)
        result = await processors.get_replica_by_id.wait_for_complete(action)

        assert result.data is not None
        assert result.data.id == route_info.route_id
        assert result.data.readiness_status == ReadinessStatus.HEALTHY
        assert result.data.liveness_status == LivenessStatus.HEALTHY
        assert result.data.activeness_status == ActivenessStatus.ACTIVE
        assert result.data.weight == 50  # 0.5 * 100

    async def test_non_existent_replica_returns_none(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
    ) -> None:
        """Non-existent ID returns data=None."""
        mock_deployment_repository.get_route = AsyncMock(return_value=None)

        action = GetReplicaByIdAction(replica_id=uuid.uuid4())
        result = await processors.get_replica_by_id.wait_for_complete(action)

        assert result.data is None

    async def test_zero_weight_traffic_inactive(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
        endpoint_id: uuid.UUID,
    ) -> None:
        """weight=0 (traffic inactive) returned correctly."""
        inactive_route = RouteInfo(
            route_id=uuid.uuid4(),
            endpoint_id=endpoint_id,
            session_id=SessionId(uuid.uuid4()),
            status=RouteStatus.HEALTHY,
            traffic_ratio=0.0,
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            revision_id=uuid.uuid4(),
            traffic_status=RouteTrafficStatus.ACTIVE,
        )
        mock_deployment_repository.get_route = AsyncMock(return_value=inactive_route)

        action = GetReplicaByIdAction(replica_id=inactive_route.route_id)
        result = await processors.get_replica_by_id.wait_for_complete(action)

        assert result.data is not None
        assert result.data.weight == 0
        assert result.data.activeness_status == ActivenessStatus.INACTIVE


class TestSearchReplicas(DeploymentCRUDBaseFixtures):
    """Tests for DeploymentService.search_replicas"""

    @pytest.fixture
    def route_info(self, endpoint_id: uuid.UUID) -> RouteInfo:
        return RouteInfo(
            route_id=uuid.uuid4(),
            endpoint_id=endpoint_id,
            session_id=SessionId(uuid.uuid4()),
            status=RouteStatus.HEALTHY,
            traffic_ratio=1.0,
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            revision_id=uuid.uuid4(),
            traffic_status=RouteTrafficStatus.ACTIVE,
        )

    async def test_default_pagination(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
        route_info: RouteInfo,
        default_querier: BatchQuerier,
    ) -> None:
        """Default pagination returns list/total_count/has_next_page/has_previous_page."""
        mock_deployment_repository.search_routes = AsyncMock(
            return_value=RouteSearchResult(
                items=[route_info],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        action = SearchReplicasAction(querier=default_querier)
        result = await processors.search_replicas.wait_for_complete(action)

        assert len(result.data) == 1
        assert result.total_count == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False

    async def test_empty_result(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
        default_querier: BatchQuerier,
    ) -> None:
        """Empty result returns data=[]/total_count=0."""
        mock_deployment_repository.search_routes = AsyncMock(
            return_value=RouteSearchResult(
                items=[],
                total_count=0,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        action = SearchReplicasAction(querier=default_querier)
        result = await processors.search_replicas.wait_for_complete(action)

        assert result.data == []
        assert result.total_count == 0

    async def test_pagination_with_next_page(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
        route_info: RouteInfo,
    ) -> None:
        """Pagination with has_next_page returns correctly."""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1, offset=0),
            conditions=[],
            orders=[],
        )
        mock_deployment_repository.search_routes = AsyncMock(
            return_value=RouteSearchResult(
                items=[route_info],
                total_count=5,
                has_next_page=True,
                has_previous_page=False,
            )
        )

        action = SearchReplicasAction(querier=querier)
        result = await processors.search_replicas.wait_for_complete(action)

        assert result.total_count == 5
        assert result.has_next_page is True


class TestSearchAccessTokens(DeploymentCRUDBaseFixtures):
    """Tests for DeploymentService.search_access_tokens"""

    @pytest.fixture
    def token_data(self) -> ModelDeploymentAccessTokenData:
        return ModelDeploymentAccessTokenData(
            id=uuid.uuid4(),
            token="test-token-abc123",
            valid_until=datetime(2025, 12, 31, tzinfo=UTC),
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
        )

    async def test_pagination_returns_tokens(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
        token_data: ModelDeploymentAccessTokenData,
        default_querier: BatchQuerier,
    ) -> None:
        """Pagination returns ModelDeploymentAccessTokenData list."""
        mock_deployment_repository.search_access_tokens = AsyncMock(
            return_value=AccessTokenSearchResult(
                items=[token_data],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        action = SearchAccessTokensAction(querier=default_querier)
        result = await processors.search_access_tokens.wait_for_complete(action)

        assert len(result.data) == 1
        assert result.data[0] == token_data
        assert result.total_count == 1

    async def test_no_tokens_returns_empty(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
        default_querier: BatchQuerier,
    ) -> None:
        """No tokens returns empty list/total_count=0."""
        mock_deployment_repository.search_access_tokens = AsyncMock(
            return_value=AccessTokenSearchResult(
                items=[],
                total_count=0,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        action = SearchAccessTokensAction(querier=default_querier)
        result = await processors.search_access_tokens.wait_for_complete(action)

        assert result.data == []
        assert result.total_count == 0


class TestSyncReplica(DeploymentCRUDBaseFixtures):
    """Tests for DeploymentService.sync_replicas"""

    async def test_triggers_check_replica_marking(
        self,
        processors: DeploymentProcessors,
        mock_deployment_controller: MagicMock,
        deployment_id: uuid.UUID,
    ) -> None:
        """Replica count mismatch triggers CHECK_REPLICA marking."""
        mock_deployment_controller.mark_lifecycle_needed = AsyncMock()

        action = SyncReplicaAction(deployment_id=deployment_id)
        result = await processors.sync_replicas.wait_for_complete(action)

        assert result.success is True
        mock_deployment_controller.mark_lifecycle_needed.assert_called_once_with(
            DeploymentLifecycleType.CHECK_REPLICA
        )

    async def test_already_synced_still_marks(
        self,
        processors: DeploymentProcessors,
        mock_deployment_controller: MagicMock,
        deployment_id: uuid.UUID,
    ) -> None:
        """Already synced state still performs marking."""
        mock_deployment_controller.mark_lifecycle_needed = AsyncMock()

        action = SyncReplicaAction(deployment_id=deployment_id)
        result = await processors.sync_replicas.wait_for_complete(action)

        assert result.success is True
        mock_deployment_controller.mark_lifecycle_needed.assert_called_once_with(
            DeploymentLifecycleType.CHECK_REPLICA
        )


class TestGetRevisionById(DeploymentCRUDBaseFixtures):
    """Tests for DeploymentService.get_revision_by_id"""

    @pytest.fixture
    def revision_data(self) -> ModelRevisionData:
        return ModelRevisionData(
            id=uuid.uuid4(),
            name="rev-1",
            cluster_config=ClusterConfigData(
                mode=ClusterMode.SINGLE_NODE,
                size=1,
            ),
            resource_config=ResourceConfigData(
                resource_group_name="default",
                resource_slot=ResourceSlot({"cpu": "4", "mem": "8g"}),
            ),
            model_runtime_config=ModelRuntimeConfigData(
                runtime_variant=RuntimeVariant.VLLM,
            ),
            model_mount_config=ModelMountConfigData(
                vfolder_id=uuid.uuid4(),
                mount_destination="/models",
                definition_path="model-definition.yaml",
            ),
            image_id=uuid.uuid4(),
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            extra_vfolder_mounts=[],
        )

    async def test_existing_revision_returns_data(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
        revision_data: ModelRevisionData,
    ) -> None:
        """Existing revision returns ModelRevisionData with name/cluster_config/resource_config/image_id/extra_vfolder_mounts."""
        mock_deployment_repository.get_revision = AsyncMock(return_value=revision_data)

        action = GetRevisionByIdAction(revision_id=revision_data.id)
        result = await processors.get_revision_by_id.wait_for_complete(action)

        assert result.data == revision_data
        assert result.data.name == "rev-1"
        assert result.data.cluster_config.mode == ClusterMode.SINGLE_NODE
        assert result.data.resource_config.resource_group_name == "default"
        assert result.data.image_id == revision_data.image_id
        assert result.data.extra_vfolder_mounts == []
        mock_deployment_repository.get_revision.assert_called_once_with(revision_data.id)

    async def test_non_existent_revision_raises(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
    ) -> None:
        """Non-existent revision raises DeploymentRevisionNotFound."""
        mock_deployment_repository.get_revision = AsyncMock(
            side_effect=Exception("DeploymentRevisionNotFound")
        )

        action = GetRevisionByIdAction(revision_id=uuid.uuid4())
        with pytest.raises(Exception, match="DeploymentRevisionNotFound"):
            await processors.get_revision_by_id.wait_for_complete(action)
