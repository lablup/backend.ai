"""
Tests for ArtifactRevisionService functionality and revision-related operations.
Tests the service layer with mocked repository operations.
Includes tests for ArtifactService methods that deal with revisions.
"""

from __future__ import annotations

import dataclasses
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.types import QuotaScopeID, QuotaScopeType, VFolderID, VFolderUsageMode
from ai.backend.manager.data.artifact.types import (
    ArtifactAvailability,
    ArtifactData,
    ArtifactDataWithRevisions,
    ArtifactRevisionData,
    ArtifactRevisionListResult,
    ArtifactRevisionReadme,
    ArtifactStatus,
    ArtifactType,
)
from ai.backend.manager.data.vfolder.types import (
    VFolderData,
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.errors.vfolder import VFolderQuotaExceededError
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.artifact_registry.repository import ArtifactRegistryRepository
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.huggingface_registry.repository import HuggingFaceRepository
from ai.backend.manager.repositories.object_storage.repository import ObjectStorageRepository
from ai.backend.manager.repositories.reservoir_registry.repository import (
    ReservoirRegistryRepository,
)
from ai.backend.manager.repositories.storage_namespace.repository import StorageNamespaceRepository
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.repositories.vfs_storage.repository import VFSStorageRepository
from ai.backend.manager.services.artifact.actions.get_revisions import (
    GetArtifactRevisionsAction,
)
from ai.backend.manager.services.artifact.actions.upsert_multi import (
    UpsertArtifactsAction,
)
from ai.backend.manager.services.artifact.service import ArtifactService
from ai.backend.manager.services.artifact_revision.actions.approve import (
    ApproveArtifactRevisionAction,
)
from ai.backend.manager.services.artifact_revision.actions.get import (
    GetArtifactRevisionAction,
)
from ai.backend.manager.services.artifact_revision.actions.get_readme import (
    GetArtifactRevisionReadmeAction,
)
from ai.backend.manager.services.artifact_revision.actions.reject import (
    RejectArtifactRevisionAction,
)
from ai.backend.manager.services.artifact_revision.actions.search import (
    SearchArtifactRevisionsAction,
)
from ai.backend.manager.services.artifact_revision.service import ArtifactRevisionService


class TestArtifactRevisionService:
    """Test cases for ArtifactRevisionService"""

    @pytest.fixture
    def mock_artifact_repository(self) -> MagicMock:
        """Create mocked ArtifactRepository"""
        return MagicMock(spec=ArtifactRepository)

    @pytest.fixture
    def mock_artifact_registry_repository(self) -> MagicMock:
        """Create mocked ArtifactRegistryRepository"""
        return MagicMock(spec=ArtifactRegistryRepository)

    @pytest.fixture
    def mock_object_storage_repository(self) -> MagicMock:
        """Create mocked ObjectStorageRepository"""
        return MagicMock(spec=ObjectStorageRepository)

    @pytest.fixture
    def mock_vfs_storage_repository(self) -> MagicMock:
        """Create mocked VFSStorageRepository"""
        return MagicMock(spec=VFSStorageRepository)

    @pytest.fixture
    def mock_storage_namespace_repository(self) -> MagicMock:
        """Create mocked StorageNamespaceRepository"""
        return MagicMock(spec=StorageNamespaceRepository)

    @pytest.fixture
    def mock_huggingface_repository(self) -> MagicMock:
        """Create mocked HuggingFaceRepository"""
        return MagicMock(spec=HuggingFaceRepository)

    @pytest.fixture
    def mock_reservoir_repository(self) -> MagicMock:
        """Create mocked ReservoirRegistryRepository"""
        return MagicMock(spec=ReservoirRegistryRepository)

    @pytest.fixture
    def mock_vfolder_repository(self) -> MagicMock:
        """Create mocked VfolderRepository"""
        return MagicMock(spec=VfolderRepository)

    @pytest.fixture
    def mock_storage_manager(self) -> MagicMock:
        """Create mocked StorageSessionManager"""
        return MagicMock()

    @pytest.fixture
    def mock_config_provider(self) -> MagicMock:
        """Create mocked ManagerConfigProvider"""
        return MagicMock()

    @pytest.fixture
    def mock_valkey_artifact_client(self) -> MagicMock:
        """Create mocked ValkeyArtifactDownloadTrackingClient"""
        return MagicMock()

    @pytest.fixture
    def mock_background_task_manager(self) -> MagicMock:
        """Create mocked BackgroundTaskManager"""
        return MagicMock()

    @pytest.fixture
    def artifact_revision_service(
        self,
        mock_artifact_repository: MagicMock,
        mock_artifact_registry_repository: MagicMock,
        mock_object_storage_repository: MagicMock,
        mock_vfs_storage_repository: MagicMock,
        mock_storage_namespace_repository: MagicMock,
        mock_huggingface_repository: MagicMock,
        mock_reservoir_repository: MagicMock,
        mock_vfolder_repository: MagicMock,
        mock_storage_manager: MagicMock,
        mock_config_provider: MagicMock,
        mock_valkey_artifact_client: MagicMock,
        mock_background_task_manager: MagicMock,
    ) -> ArtifactRevisionService:
        """Create ArtifactRevisionService instance with mocked repositories"""
        return ArtifactRevisionService(
            artifact_repository=mock_artifact_repository,
            artifact_registry_repository=mock_artifact_registry_repository,
            object_storage_repository=mock_object_storage_repository,
            vfs_storage_repository=mock_vfs_storage_repository,
            storage_namespace_repository=mock_storage_namespace_repository,
            huggingface_registry_repository=mock_huggingface_repository,
            reservoir_registry_repository=mock_reservoir_repository,
            vfolder_repository=mock_vfolder_repository,
            storage_manager=mock_storage_manager,
            config_provider=mock_config_provider,
            valkey_artifact_client=mock_valkey_artifact_client,
            background_task_manager=mock_background_task_manager,
        )

    @pytest.fixture
    def sample_artifact_revision_data(self) -> ArtifactRevisionData:
        """Create sample artifact revision data"""
        now = datetime.now(UTC)
        return ArtifactRevisionData(
            id=uuid.uuid4(),
            artifact_id=uuid.uuid4(),
            version="main",
            readme="# DialoGPT-medium\n\nA conversational AI model.",
            size=1024000,
            status=ArtifactStatus.AVAILABLE,
            remote_status=None,
            created_at=now,
            updated_at=now,
            digest=None,
            verification_result=None,
        )

    async def test_get_artifact_revision(
        self,
        artifact_revision_service: ArtifactRevisionService,
        mock_artifact_repository: MagicMock,
        sample_artifact_revision_data: ArtifactRevisionData,
    ) -> None:
        """Test getting an artifact revision by ID"""
        mock_artifact_repository.get_artifact_revision_by_id = AsyncMock(
            return_value=sample_artifact_revision_data
        )

        action = GetArtifactRevisionAction(artifact_revision_id=sample_artifact_revision_data.id)
        result = await artifact_revision_service.get(action)

        assert result.revision == sample_artifact_revision_data
        mock_artifact_repository.get_artifact_revision_by_id.assert_called_once_with(
            sample_artifact_revision_data.id
        )

    async def test_get_artifact_revision_readme(
        self,
        artifact_revision_service: ArtifactRevisionService,
        mock_artifact_repository: MagicMock,
        sample_artifact_revision_data: ArtifactRevisionData,
    ) -> None:
        """Test getting artifact revision readme"""
        expected_readme = "# DialoGPT-medium\n\nA conversational AI model."
        mock_artifact_repository.get_artifact_revision_readme = AsyncMock(
            return_value=expected_readme
        )

        action = GetArtifactRevisionReadmeAction(
            artifact_revision_id=sample_artifact_revision_data.id
        )
        result = await artifact_revision_service.get_readme(action)

        assert result.readme_data == ArtifactRevisionReadme(readme=expected_readme)
        mock_artifact_repository.get_artifact_revision_readme.assert_called_once_with(
            sample_artifact_revision_data.id
        )

    async def test_search_artifact_revisions(
        self,
        artifact_revision_service: ArtifactRevisionService,
        mock_artifact_repository: MagicMock,
        sample_artifact_revision_data: ArtifactRevisionData,
    ) -> None:
        """Test searching artifact revisions with querier"""
        mock_artifact_repository.search_artifact_revisions = AsyncMock(
            return_value=ArtifactRevisionListResult(
                items=[sample_artifact_revision_data],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        action = SearchArtifactRevisionsAction(querier=querier)
        result = await artifact_revision_service.search_revision(action)

        assert result.data == [sample_artifact_revision_data]
        assert result.total_count == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False
        mock_artifact_repository.search_artifact_revisions.assert_called_once_with(querier=querier)

    async def test_search_artifact_revisions_empty_result(
        self,
        artifact_revision_service: ArtifactRevisionService,
        mock_artifact_repository: MagicMock,
    ) -> None:
        """Test searching artifact revisions when no results are found"""
        mock_artifact_repository.search_artifact_revisions = AsyncMock(
            return_value=ArtifactRevisionListResult(
                items=[],
                total_count=0,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        action = SearchArtifactRevisionsAction(querier=querier)
        result = await artifact_revision_service.search_revision(action)

        assert result.data == []
        assert result.total_count == 0

    async def test_search_artifact_revisions_with_pagination(
        self,
        artifact_revision_service: ArtifactRevisionService,
        mock_artifact_repository: MagicMock,
        sample_artifact_revision_data: ArtifactRevisionData,
    ) -> None:
        """Test searching artifact revisions with pagination"""
        mock_artifact_repository.search_artifact_revisions = AsyncMock(
            return_value=ArtifactRevisionListResult(
                items=[sample_artifact_revision_data],
                total_count=25,
                has_next_page=True,
                has_previous_page=True,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=10),
            conditions=[],
            orders=[],
        )
        action = SearchArtifactRevisionsAction(querier=querier)
        result = await artifact_revision_service.search_revision(action)

        assert result.total_count == 25
        assert result.has_next_page is True
        assert result.has_previous_page is True

    async def test_approve_artifact_revision(
        self,
        artifact_revision_service: ArtifactRevisionService,
        mock_artifact_repository: MagicMock,
        sample_artifact_revision_data: ArtifactRevisionData,
    ) -> None:
        """Test approving an artifact revision"""
        approved_revision = ArtifactRevisionData(
            id=sample_artifact_revision_data.id,
            artifact_id=sample_artifact_revision_data.artifact_id,
            version=sample_artifact_revision_data.version,
            readme=sample_artifact_revision_data.readme,
            size=sample_artifact_revision_data.size,
            status=ArtifactStatus.AVAILABLE,
            remote_status=None,
            created_at=sample_artifact_revision_data.created_at,
            updated_at=datetime.now(UTC),
            digest=sample_artifact_revision_data.digest,
            verification_result=sample_artifact_revision_data.verification_result,
        )
        mock_artifact_repository.approve_artifact = AsyncMock(return_value=approved_revision)

        action = ApproveArtifactRevisionAction(
            artifact_revision_id=sample_artifact_revision_data.id
        )
        result = await artifact_revision_service.approve(action)

        assert result.result.status == ArtifactStatus.AVAILABLE
        mock_artifact_repository.approve_artifact.assert_called_once_with(
            sample_artifact_revision_data.id
        )

    async def test_reject_artifact_revision(
        self,
        artifact_revision_service: ArtifactRevisionService,
        mock_artifact_repository: MagicMock,
        sample_artifact_revision_data: ArtifactRevisionData,
    ) -> None:
        """Test rejecting an artifact revision"""
        rejected_revision = ArtifactRevisionData(
            id=sample_artifact_revision_data.id,
            artifact_id=sample_artifact_revision_data.artifact_id,
            version=sample_artifact_revision_data.version,
            readme=sample_artifact_revision_data.readme,
            size=sample_artifact_revision_data.size,
            status=ArtifactStatus.REJECTED,
            remote_status=None,
            created_at=sample_artifact_revision_data.created_at,
            updated_at=datetime.now(UTC),
            digest=sample_artifact_revision_data.digest,
            verification_result=sample_artifact_revision_data.verification_result,
        )
        mock_artifact_repository.reject_artifact = AsyncMock(return_value=rejected_revision)

        action = RejectArtifactRevisionAction(artifact_revision_id=sample_artifact_revision_data.id)
        result = await artifact_revision_service.reject(action)

        assert result.result.status == ArtifactStatus.REJECTED
        mock_artifact_repository.reject_artifact.assert_called_once_with(
            sample_artifact_revision_data.id
        )


class TestArtifactServiceRevisionOperations:
    """Test cases for ArtifactService methods that deal with revisions"""

    @pytest.fixture
    def mock_artifact_repository(self) -> MagicMock:
        """Create mocked ArtifactRepository"""
        return MagicMock(spec=ArtifactRepository)

    @pytest.fixture
    def mock_artifact_registry_repository(self) -> MagicMock:
        """Create mocked ArtifactRegistryRepository"""
        return MagicMock(spec=ArtifactRegistryRepository)

    @pytest.fixture
    def mock_object_storage_repository(self) -> MagicMock:
        """Create mocked ObjectStorageRepository"""
        return MagicMock(spec=ObjectStorageRepository)

    @pytest.fixture
    def mock_vfs_storage_repository(self) -> MagicMock:
        """Create mocked VFSStorageRepository"""
        return MagicMock(spec=VFSStorageRepository)

    @pytest.fixture
    def mock_huggingface_repository(self) -> MagicMock:
        """Create mocked HuggingFaceRepository"""
        return MagicMock(spec=HuggingFaceRepository)

    @pytest.fixture
    def mock_reservoir_repository(self) -> MagicMock:
        """Create mocked ReservoirRegistryRepository"""
        return MagicMock(spec=ReservoirRegistryRepository)

    @pytest.fixture
    def mock_vfolder_repository(self) -> MagicMock:
        """Create mocked VfolderRepository"""
        return MagicMock(spec=VfolderRepository)

    @pytest.fixture
    def mock_storage_manager(self) -> MagicMock:
        """Create mocked StorageSessionManager"""
        return MagicMock()

    @pytest.fixture
    def mock_config_provider(self) -> MagicMock:
        """Create mocked ManagerConfigProvider"""
        return MagicMock()

    @pytest.fixture
    def artifact_service(
        self,
        mock_artifact_repository: MagicMock,
        mock_artifact_registry_repository: MagicMock,
        mock_object_storage_repository: MagicMock,
        mock_vfs_storage_repository: MagicMock,
        mock_huggingface_repository: MagicMock,
        mock_reservoir_repository: MagicMock,
        mock_storage_manager: MagicMock,
        mock_config_provider: MagicMock,
    ) -> ArtifactService:
        """Create ArtifactService instance with mocked repositories"""
        return ArtifactService(
            artifact_repository=mock_artifact_repository,
            artifact_registry_repository=mock_artifact_registry_repository,
            object_storage_repository=mock_object_storage_repository,
            vfs_storage_repository=mock_vfs_storage_repository,
            huggingface_registry_repository=mock_huggingface_repository,
            reservoir_registry_repository=mock_reservoir_repository,
            storage_manager=mock_storage_manager,
            config_provider=mock_config_provider,
        )

    @pytest.fixture
    def sample_artifact_data(self) -> ArtifactData:
        """Create sample artifact data"""
        now = datetime.now(UTC)
        registry_id = uuid.uuid4()
        return ArtifactData(
            id=uuid.uuid4(),
            name="microsoft/DialoGPT-medium",
            type=ArtifactType.MODEL,
            description="A conversational AI model by Microsoft",
            registry_id=registry_id,
            source_registry_id=registry_id,
            registry_type=ArtifactRegistryType.HUGGINGFACE,
            source_registry_type=ArtifactRegistryType.HUGGINGFACE,
            availability=ArtifactAvailability.ALIVE,
            scanned_at=now,
            updated_at=now,
            readonly=True,
            extra=None,
        )

    @pytest.fixture
    def sample_artifact_revision(self, sample_artifact_data: ArtifactData) -> ArtifactRevisionData:
        """Create sample artifact revision data"""
        now = datetime.now(UTC)
        return ArtifactRevisionData(
            id=uuid.uuid4(),
            artifact_id=sample_artifact_data.id,
            version="main",
            readme="# DialoGPT-medium\n\nA conversational AI model.",
            size=1024000,
            status=ArtifactStatus.AVAILABLE,
            remote_status=None,
            created_at=now,
            updated_at=now,
            digest=None,
            verification_result=None,
        )

    async def test_get_artifact_revisions(
        self,
        artifact_service: ArtifactService,
        mock_artifact_repository: MagicMock,
        sample_artifact_data: ArtifactData,
        sample_artifact_revision: ArtifactRevisionData,
    ) -> None:
        """Test getting artifact revisions via ArtifactService"""
        mock_artifact_repository.list_artifact_revisions = AsyncMock(
            return_value=[sample_artifact_revision]
        )

        action = GetArtifactRevisionsAction(artifact_id=sample_artifact_data.id)
        result = await artifact_service.get_revisions(action)

        assert result.revisions == [sample_artifact_revision]
        mock_artifact_repository.list_artifact_revisions.assert_called_once_with(
            sample_artifact_data.id
        )

    async def test_upsert_artifacts_with_revisions(
        self,
        artifact_service: ArtifactService,
        mock_artifact_repository: MagicMock,
        sample_artifact_data: ArtifactData,
        sample_artifact_revision: ArtifactRevisionData,
    ) -> None:
        """Test upserting artifacts with revisions via ArtifactService"""
        artifact_with_revisions = ArtifactDataWithRevisions(
            id=sample_artifact_data.id,
            name=sample_artifact_data.name,
            type=sample_artifact_data.type,
            description=sample_artifact_data.description,
            registry_id=sample_artifact_data.registry_id,
            source_registry_id=sample_artifact_data.source_registry_id,
            registry_type=sample_artifact_data.registry_type,
            source_registry_type=sample_artifact_data.source_registry_type,
            availability=sample_artifact_data.availability,
            scanned_at=sample_artifact_data.scanned_at,
            updated_at=sample_artifact_data.updated_at,
            readonly=sample_artifact_data.readonly,
            extra=sample_artifact_data.extra,
            revisions=[sample_artifact_revision],
        )

        mock_artifact_repository.upsert_artifacts = AsyncMock(return_value=[sample_artifact_data])
        mock_artifact_repository.upsert_artifact_revisions = AsyncMock(
            return_value=[sample_artifact_revision]
        )

        action = UpsertArtifactsAction(data=[artifact_with_revisions])
        result = await artifact_service.upsert_artifacts_with_revisions(action)

        assert len(result.result) == 1
        assert result.result[0].revisions == [sample_artifact_revision]
        mock_artifact_repository.upsert_artifacts.assert_called_once()
        mock_artifact_repository.upsert_artifact_revisions.assert_called_once()


class TestVFolderQuotaCheck:
    """Tests for VFolder quota validation in ArtifactRevisionService."""

    @pytest.fixture
    def mock_artifact_repository(self) -> MagicMock:
        return MagicMock(spec=ArtifactRepository)

    @pytest.fixture
    def mock_artifact_registry_repository(self) -> MagicMock:
        return MagicMock(spec=ArtifactRegistryRepository)

    @pytest.fixture
    def mock_object_storage_repository(self) -> MagicMock:
        return MagicMock(spec=ObjectStorageRepository)

    @pytest.fixture
    def mock_vfs_storage_repository(self) -> MagicMock:
        return MagicMock(spec=VFSStorageRepository)

    @pytest.fixture
    def mock_storage_namespace_repository(self) -> MagicMock:
        return MagicMock(spec=StorageNamespaceRepository)

    @pytest.fixture
    def mock_huggingface_repository(self) -> MagicMock:
        return MagicMock(spec=HuggingFaceRepository)

    @pytest.fixture
    def mock_reservoir_repository(self) -> MagicMock:
        return MagicMock(spec=ReservoirRegistryRepository)

    @pytest.fixture
    def mock_vfolder_repository(self) -> MagicMock:
        return MagicMock(spec=VfolderRepository)

    @pytest.fixture
    def mock_storage_manager(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def mock_config_provider(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def mock_valkey_artifact_client(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def mock_background_task_manager(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def artifact_revision_service(
        self,
        mock_artifact_repository: MagicMock,
        mock_artifact_registry_repository: MagicMock,
        mock_object_storage_repository: MagicMock,
        mock_vfs_storage_repository: MagicMock,
        mock_storage_namespace_repository: MagicMock,
        mock_huggingface_repository: MagicMock,
        mock_reservoir_repository: MagicMock,
        mock_vfolder_repository: MagicMock,
        mock_storage_manager: MagicMock,
        mock_config_provider: MagicMock,
        mock_valkey_artifact_client: MagicMock,
        mock_background_task_manager: MagicMock,
    ) -> ArtifactRevisionService:
        return ArtifactRevisionService(
            artifact_repository=mock_artifact_repository,
            artifact_registry_repository=mock_artifact_registry_repository,
            object_storage_repository=mock_object_storage_repository,
            vfs_storage_repository=mock_vfs_storage_repository,
            storage_namespace_repository=mock_storage_namespace_repository,
            huggingface_registry_repository=mock_huggingface_repository,
            reservoir_registry_repository=mock_reservoir_repository,
            vfolder_repository=mock_vfolder_repository,
            storage_manager=mock_storage_manager,
            config_provider=mock_config_provider,
            valkey_artifact_client=mock_valkey_artifact_client,
            background_task_manager=mock_background_task_manager,
        )

    @pytest.fixture
    def sample_vfolder_data(self) -> VFolderData:
        """Create sample VFolderData with quota scope."""
        return VFolderData(
            id=uuid.uuid4(),
            name="test-vfolder",
            host="local:volume1",
            domain_name="default",
            quota_scope_id=QuotaScopeID(QuotaScopeType.USER, uuid.uuid4()),
            usage_mode=VFolderUsageMode.MODEL,
            permission=VFolderMountPermission.RW_DELETE,
            max_files=1000,
            max_size=1024 * 1024 * 1024,
            num_files=10,
            cur_size=100 * 1024 * 1024,
            created_at=datetime.now(UTC),
            last_used=None,
            creator="testuser@example.com",
            unmanaged_path=None,
            ownership_type=VFolderOwnershipType.USER,
            user=uuid.uuid4(),
            group=None,
            cloneable=False,
            status=VFolderOperationStatus.READY,
        )

    async def test_check_vfolder_quota_no_quota_scope(
        self,
        artifact_revision_service: ArtifactRevisionService,
        sample_vfolder_data: VFolderData,
    ) -> None:
        """When quota_scope_id is None, quota check should be skipped."""
        vfolder_data = dataclasses.replace(sample_vfolder_data, quota_scope_id=None)

        # Should not raise any error
        await artifact_revision_service._check_vfolder_quota(vfolder_data, 500 * 1024 * 1024)

    async def test_check_vfolder_quota_unlimited_negative_one(
        self,
        artifact_revision_service: ArtifactRevisionService,
        mock_storage_manager: MagicMock,
        mock_vfolder_repository: MagicMock,
        sample_vfolder_data: VFolderData,
    ) -> None:
        """When max quota is -1 (unlimited), should not raise error."""
        mock_storage_manager.get_proxy_and_volume.return_value = ("proxy", "volume1")
        mock_storage_client = AsyncMock()
        mock_storage_client.get_quota_scope = AsyncMock(
            return_value={"used_bytes": 500 * 1024 * 1024}
        )
        mock_storage_manager.get_manager_facing_client.return_value = mock_storage_client

        mock_vfolder_repository.get_user_resource_info = AsyncMock(
            return_value=("user_uuid", -1, "policy")
        )

        # Should not raise any error even with large additional size
        await artifact_revision_service._check_vfolder_quota(
            sample_vfolder_data, 10 * 1024 * 1024 * 1024
        )

    async def test_check_vfolder_quota_unlimited_zero(
        self,
        artifact_revision_service: ArtifactRevisionService,
        mock_storage_manager: MagicMock,
        mock_vfolder_repository: MagicMock,
        sample_vfolder_data: VFolderData,
    ) -> None:
        """When max quota is 0 (unlimited), should not raise error."""
        mock_storage_manager.get_proxy_and_volume.return_value = ("proxy", "volume1")
        mock_storage_client = AsyncMock()
        mock_storage_client.get_quota_scope = AsyncMock(
            return_value={"used_bytes": 500 * 1024 * 1024}
        )
        mock_storage_manager.get_manager_facing_client.return_value = mock_storage_client

        mock_vfolder_repository.get_user_resource_info = AsyncMock(
            return_value=("user_uuid", 0, "policy")
        )

        await artifact_revision_service._check_vfolder_quota(
            sample_vfolder_data, 10 * 1024 * 1024 * 1024
        )

    async def test_check_vfolder_quota_within_limit(
        self,
        artifact_revision_service: ArtifactRevisionService,
        mock_storage_manager: MagicMock,
        mock_vfolder_repository: MagicMock,
        sample_vfolder_data: VFolderData,
    ) -> None:
        """When within quota limit, should not raise error."""
        mock_storage_manager.get_proxy_and_volume.return_value = ("proxy", "volume1")
        mock_storage_client = AsyncMock()
        mock_storage_client.get_quota_scope = AsyncMock(
            return_value={"used_bytes": 100 * 1024 * 1024}
        )
        mock_storage_manager.get_manager_facing_client.return_value = mock_storage_client

        mock_vfolder_repository.get_user_resource_info = AsyncMock(
            return_value=("user_uuid", 1024 * 1024 * 1024, "policy")
        )

        # 100MB (used) + 500MB (additional) < 1GB (max) → OK
        await artifact_revision_service._check_vfolder_quota(sample_vfolder_data, 500 * 1024 * 1024)

    async def test_check_vfolder_quota_exactly_at_limit(
        self,
        artifact_revision_service: ArtifactRevisionService,
        mock_storage_manager: MagicMock,
        mock_vfolder_repository: MagicMock,
        sample_vfolder_data: VFolderData,
    ) -> None:
        """When exactly at quota limit, should not raise error."""
        mock_storage_manager.get_proxy_and_volume.return_value = ("proxy", "volume1")
        mock_storage_client = AsyncMock()
        mock_storage_client.get_quota_scope = AsyncMock(
            return_value={"used_bytes": 500 * 1024 * 1024}
        )
        mock_storage_manager.get_manager_facing_client.return_value = mock_storage_client

        mock_vfolder_repository.get_user_resource_info = AsyncMock(
            return_value=("user_uuid", 1024 * 1024 * 1024, "policy")
        )

        # 500MB (used) + 524MB (additional) = 1024MB (max) → OK (exactly at limit)
        await artifact_revision_service._check_vfolder_quota(sample_vfolder_data, 524 * 1024 * 1024)

    async def test_check_vfolder_quota_exceeded(
        self,
        artifact_revision_service: ArtifactRevisionService,
        mock_storage_manager: MagicMock,
        mock_vfolder_repository: MagicMock,
        sample_vfolder_data: VFolderData,
    ) -> None:
        """When quota would be exceeded, should raise VFolderQuotaExceededError."""
        mock_storage_manager.get_proxy_and_volume.return_value = ("proxy", "volume1")
        mock_storage_client = AsyncMock()
        mock_storage_client.get_quota_scope = AsyncMock(
            return_value={"used_bytes": 900 * 1024 * 1024}
        )
        mock_storage_manager.get_manager_facing_client.return_value = mock_storage_client

        mock_vfolder_repository.get_user_resource_info = AsyncMock(
            return_value=("user_uuid", 1024 * 1024 * 1024, "policy")
        )

        # 900MB (used) + 200MB (additional) > 1GB (max) → Error
        with pytest.raises(VFolderQuotaExceededError) as exc_info:
            await artifact_revision_service._check_vfolder_quota(
                sample_vfolder_data, 200 * 1024 * 1024
            )

        error = exc_info.value
        assert error.current_size == 900 * 1024 * 1024
        assert error.max_size == 1024 * 1024 * 1024
        assert error.requested_size == 200 * 1024 * 1024

    async def test_check_vfolder_quota_project_scope(
        self,
        artifact_revision_service: ArtifactRevisionService,
        mock_storage_manager: MagicMock,
        mock_vfolder_repository: MagicMock,
        sample_vfolder_data: VFolderData,
    ) -> None:
        """Test quota check with PROJECT scope type."""
        project_id = uuid.uuid4()
        vfolder_data = dataclasses.replace(
            sample_vfolder_data,
            quota_scope_id=QuotaScopeID(QuotaScopeType.PROJECT, project_id),
        )

        mock_storage_manager.get_proxy_and_volume.return_value = ("proxy", "volume1")
        mock_storage_client = AsyncMock()
        mock_storage_client.get_quota_scope = AsyncMock(
            return_value={"used_bytes": 100 * 1024 * 1024}
        )
        mock_storage_manager.get_manager_facing_client.return_value = mock_storage_client

        mock_vfolder_repository.get_group_resource_info = AsyncMock(
            return_value=("group_name", "domain", 2 * 1024 * 1024 * 1024, "policy")
        )

        # Should not raise error
        await artifact_revision_service._check_vfolder_quota(vfolder_data, 500 * 1024 * 1024)

        mock_vfolder_repository.get_group_resource_info.assert_called_once_with(
            project_id, "default"
        )


class TestGetQuotaScopeLimit:
    """Tests for _get_quota_scope_limit method."""

    @pytest.fixture
    def mock_artifact_repository(self) -> MagicMock:
        return MagicMock(spec=ArtifactRepository)

    @pytest.fixture
    def mock_artifact_registry_repository(self) -> MagicMock:
        return MagicMock(spec=ArtifactRegistryRepository)

    @pytest.fixture
    def mock_object_storage_repository(self) -> MagicMock:
        return MagicMock(spec=ObjectStorageRepository)

    @pytest.fixture
    def mock_vfs_storage_repository(self) -> MagicMock:
        return MagicMock(spec=VFSStorageRepository)

    @pytest.fixture
    def mock_storage_namespace_repository(self) -> MagicMock:
        return MagicMock(spec=StorageNamespaceRepository)

    @pytest.fixture
    def mock_huggingface_repository(self) -> MagicMock:
        return MagicMock(spec=HuggingFaceRepository)

    @pytest.fixture
    def mock_reservoir_repository(self) -> MagicMock:
        return MagicMock(spec=ReservoirRegistryRepository)

    @pytest.fixture
    def mock_vfolder_repository(self) -> MagicMock:
        return MagicMock(spec=VfolderRepository)

    @pytest.fixture
    def mock_storage_manager(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def mock_config_provider(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def mock_valkey_artifact_client(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def mock_background_task_manager(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def artifact_revision_service(
        self,
        mock_artifact_repository: MagicMock,
        mock_artifact_registry_repository: MagicMock,
        mock_object_storage_repository: MagicMock,
        mock_vfs_storage_repository: MagicMock,
        mock_storage_namespace_repository: MagicMock,
        mock_huggingface_repository: MagicMock,
        mock_reservoir_repository: MagicMock,
        mock_vfolder_repository: MagicMock,
        mock_storage_manager: MagicMock,
        mock_config_provider: MagicMock,
        mock_valkey_artifact_client: MagicMock,
        mock_background_task_manager: MagicMock,
    ) -> ArtifactRevisionService:
        return ArtifactRevisionService(
            artifact_repository=mock_artifact_repository,
            artifact_registry_repository=mock_artifact_registry_repository,
            object_storage_repository=mock_object_storage_repository,
            vfs_storage_repository=mock_vfs_storage_repository,
            storage_namespace_repository=mock_storage_namespace_repository,
            huggingface_registry_repository=mock_huggingface_repository,
            reservoir_registry_repository=mock_reservoir_repository,
            vfolder_repository=mock_vfolder_repository,
            storage_manager=mock_storage_manager,
            config_provider=mock_config_provider,
            valkey_artifact_client=mock_valkey_artifact_client,
            background_task_manager=mock_background_task_manager,
        )

    async def test_get_quota_scope_limit_user_type(
        self,
        artifact_revision_service: ArtifactRevisionService,
        mock_vfolder_repository: MagicMock,
    ) -> None:
        """Test _get_quota_scope_limit with USER scope type."""
        user_id = uuid.uuid4()
        quota_scope_id = QuotaScopeID(QuotaScopeType.USER, user_id)

        mock_vfolder_repository.get_user_resource_info = AsyncMock(
            return_value=("user_uuid", 1024 * 1024 * 1024, "policy")
        )

        result = await artifact_revision_service._get_quota_scope_limit(quota_scope_id, "default")

        assert result == 1024 * 1024 * 1024
        mock_vfolder_repository.get_user_resource_info.assert_called_once_with(user_id)

    async def test_get_quota_scope_limit_project_type(
        self,
        artifact_revision_service: ArtifactRevisionService,
        mock_vfolder_repository: MagicMock,
    ) -> None:
        """Test _get_quota_scope_limit with PROJECT scope type."""
        project_id = uuid.uuid4()
        quota_scope_id = QuotaScopeID(QuotaScopeType.PROJECT, project_id)

        mock_vfolder_repository.get_group_resource_info = AsyncMock(
            return_value=("group_name", "domain", 2 * 1024 * 1024 * 1024, "policy")
        )

        result = await artifact_revision_service._get_quota_scope_limit(quota_scope_id, "default")

        assert result == 2 * 1024 * 1024 * 1024
        mock_vfolder_repository.get_group_resource_info.assert_called_once_with(
            project_id, "default"
        )

    async def test_get_quota_scope_limit_user_not_found(
        self,
        artifact_revision_service: ArtifactRevisionService,
        mock_vfolder_repository: MagicMock,
    ) -> None:
        """When user is not found, should return -1 (unlimited)."""
        user_id = uuid.uuid4()
        quota_scope_id = QuotaScopeID(QuotaScopeType.USER, user_id)

        mock_vfolder_repository.get_user_resource_info = AsyncMock(return_value=None)

        result = await artifact_revision_service._get_quota_scope_limit(quota_scope_id, "default")

        assert result == -1

    async def test_get_quota_scope_limit_project_not_found(
        self,
        artifact_revision_service: ArtifactRevisionService,
        mock_vfolder_repository: MagicMock,
    ) -> None:
        """When project is not found, should return -1 (unlimited)."""
        project_id = uuid.uuid4()
        quota_scope_id = QuotaScopeID(QuotaScopeType.PROJECT, project_id)

        mock_vfolder_repository.get_group_resource_info = AsyncMock(return_value=None)

        result = await artifact_revision_service._get_quota_scope_limit(quota_scope_id, "default")

        assert result == -1


class TestVFolderQuotaExceededError:
    """Tests for VFolderQuotaExceededError."""

    def test_error_message_format(self) -> None:
        """Test error message contains all relevant information."""
        quota_scope_id = QuotaScopeID(QuotaScopeType.USER, uuid.uuid4())
        vfolder_id = VFolderID(quota_scope_id, uuid.uuid4())

        error = VFolderQuotaExceededError(
            vfolder_id=vfolder_id,
            quota_scope_id=quota_scope_id,
            current_size=900,
            max_size=1000,
            requested_size=200,
        )

        error_message = str(error)
        assert "900" in error_message
        assert "1000" in error_message
        assert "200" in error_message
        assert "100" in error_message  # available bytes

    def test_error_data_structure(self) -> None:
        """Test error_data returns correct structure."""
        quota_scope_id = QuotaScopeID(QuotaScopeType.USER, uuid.uuid4())
        vfolder_id = VFolderID(quota_scope_id, uuid.uuid4())

        error = VFolderQuotaExceededError(
            vfolder_id=vfolder_id,
            quota_scope_id=quota_scope_id,
            current_size=900,
            max_size=1000,
            requested_size=200,
        )

        data = error.error_data()
        assert data["current_size_bytes"] == 900
        assert data["max_size_bytes"] == 1000
        assert data["requested_size_bytes"] == 200
        assert data["available_bytes"] == 100

    def test_error_code(self) -> None:
        """Test error_code returns correct ErrorCode."""
        quota_scope_id = QuotaScopeID(QuotaScopeType.USER, uuid.uuid4())
        vfolder_id = VFolderID(quota_scope_id, uuid.uuid4())

        error = VFolderQuotaExceededError(
            vfolder_id=vfolder_id,
            quota_scope_id=quota_scope_id,
            current_size=900,
            max_size=1000,
            requested_size=200,
        )

        error_code = error.error_code()
        assert error_code is not None
