"""
Tests for ArtifactRevisionService functionality and revision-related operations.
Tests the service layer with mocked repository operations.
Includes tests for ArtifactService methods that deal with revisions.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.data.artifact.types import (
    ArtifactRegistryType,
    ArtifactRevisionDownloadProgress,
)
from ai.backend.common.data.storage.types import ArtifactStorageType
from ai.backend.manager.data.artifact.types import (
    ArtifactAvailability,
    ArtifactData,
    ArtifactDataWithRevisions,
    ArtifactRemoteStatus,
    ArtifactRevisionData,
    ArtifactRevisionListResult,
    ArtifactRevisionReadme,
    ArtifactStatus,
    ArtifactType,
)
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryData
from ai.backend.manager.data.association.types import AssociationArtifactsStoragesData
from ai.backend.manager.errors.artifact import (
    ArtifactDeletionBadRequestError,
    ArtifactImportBadRequestError,
)
from ai.backend.manager.errors.artifact_registry import InvalidArtifactRegistryTypeError
from ai.backend.manager.errors.common import ServerMisconfiguredError
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
from ai.backend.manager.services.artifact_revision.actions.associate_with_storage import (
    AssociateWithStorageAction,
)
from ai.backend.manager.services.artifact_revision.actions.cancel_import import (
    CancelImportAction,
)
from ai.backend.manager.services.artifact_revision.actions.cleanup import (
    CleanupArtifactRevisionAction,
)
from ai.backend.manager.services.artifact_revision.actions.delegate_import_revision_batch import (
    DelegateImportArtifactRevisionBatchAction,
)
from ai.backend.manager.services.artifact_revision.actions.disassociate_with_storage import (
    DisassociateWithStorageAction,
)
from ai.backend.manager.services.artifact_revision.actions.get import (
    GetArtifactRevisionAction,
)
from ai.backend.manager.services.artifact_revision.actions.get_download_progress import (
    GetDownloadProgressAction,
)
from ai.backend.manager.services.artifact_revision.actions.get_readme import (
    GetArtifactRevisionReadmeAction,
)
from ai.backend.manager.services.artifact_revision.actions.import_revision import (
    ImportArtifactRevisionAction,
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


class TestImportArtifactRevisionAction:
    """Test cases for ImportArtifactRevisionAction"""

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
    def service(
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
    def sample_revision(self) -> ArtifactRevisionData:
        now = datetime.now(UTC)
        return ArtifactRevisionData(
            id=uuid.uuid4(),
            artifact_id=uuid.uuid4(),
            version="main",
            readme="# Model",
            size=1024000,
            status=ArtifactStatus.AVAILABLE,
            remote_status=None,
            created_at=now,
            updated_at=now,
            digest="abc123hash",
            verification_result=None,
        )

    @pytest.fixture
    def sample_artifact(self, sample_revision: ArtifactRevisionData) -> ArtifactData:
        now = datetime.now(UTC)
        registry_id = uuid.uuid4()
        return ArtifactData(
            id=sample_revision.artifact_id,
            name="microsoft/DialoGPT-medium",
            type=ArtifactType.MODEL,
            description="A model",
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

    def _setup_reservoir_config(
        self,
        mock_config_provider: MagicMock,
        *,
        use_delegation: bool = False,
    ) -> MagicMock:
        reservoir_cfg = MagicMock()
        reservoir_cfg.use_delegation = use_delegation
        reservoir_cfg.archive_storage = "test-storage"
        reservoir_cfg.config.storage_type = ArtifactStorageType.OBJECT_STORAGE.value
        reservoir_cfg.config.bucket_name = "test-bucket"
        reservoir_cfg.resolve_storage_step_selection.return_value = {}
        mock_config_provider.config.reservoir = reservoir_cfg
        return reservoir_cfg

    def _setup_storage_mocks(
        self,
        mock_object_storage_repository: MagicMock,
        mock_storage_namespace_repository: MagicMock,
        mock_storage_manager: MagicMock,
    ) -> tuple[MagicMock, uuid.UUID]:
        namespace_id = uuid.uuid4()
        storage_data = MagicMock()
        storage_data.id = uuid.uuid4()
        storage_data.host = "storage-host"
        storage_data.name = "test-storage"
        mock_object_storage_repository.get_by_name = AsyncMock(return_value=storage_data)

        namespace_data = MagicMock()
        namespace_data.id = namespace_id
        namespace_data.namespace = "test-bucket"
        mock_storage_namespace_repository.get_by_storage_and_namespace = AsyncMock(
            return_value=namespace_data
        )

        storage_proxy_client = MagicMock()
        mock_storage_manager.get_manager_facing_client.return_value = storage_proxy_client
        return storage_proxy_client, namespace_id

    async def test_huggingface_available_matching_hash_no_force_returns_early(
        self,
        service: ArtifactRevisionService,
        mock_artifact_repository: MagicMock,
        mock_huggingface_repository: MagicMock,
        mock_object_storage_repository: MagicMock,
        mock_storage_namespace_repository: MagicMock,
        mock_storage_manager: MagicMock,
        mock_config_provider: MagicMock,
        sample_revision: ArtifactRevisionData,
        sample_artifact: ArtifactData,
    ) -> None:
        """HuggingFace: AVAILABLE + matching commit hash + force=False returns early"""
        mock_artifact_repository.get_artifact_revision_by_id = AsyncMock(
            return_value=sample_revision
        )
        mock_artifact_repository.get_artifact_by_id = AsyncMock(return_value=sample_artifact)
        self._setup_reservoir_config(mock_config_provider)
        storage_proxy_client, _ = self._setup_storage_mocks(
            mock_object_storage_repository, mock_storage_namespace_repository, mock_storage_manager
        )

        hf_data = MagicMock()
        hf_data.name = "hf-registry"
        mock_huggingface_repository.get_registry_data_by_artifact_id = AsyncMock(
            return_value=hf_data
        )

        commit_hash_resp = MagicMock()
        commit_hash_resp.commit_hash = "abc123hash"
        storage_proxy_client.get_huggingface_model_commit_hash = AsyncMock(
            return_value=commit_hash_resp
        )

        action = ImportArtifactRevisionAction(artifact_revision_id=sample_revision.id, force=False)
        result = await service.import_revision(action)

        assert result.result == sample_revision
        assert result.task_id is None
        mock_artifact_repository.update_artifact_revision_status.assert_not_called()

    async def test_huggingface_force_true_always_downloads(
        self,
        service: ArtifactRevisionService,
        mock_artifact_repository: MagicMock,
        mock_huggingface_repository: MagicMock,
        mock_object_storage_repository: MagicMock,
        mock_storage_namespace_repository: MagicMock,
        mock_storage_manager: MagicMock,
        mock_config_provider: MagicMock,
        sample_revision: ArtifactRevisionData,
        sample_artifact: ArtifactData,
    ) -> None:
        """HuggingFace: force=True always downloads even if hash matches"""
        mock_artifact_repository.get_artifact_revision_by_id = AsyncMock(
            return_value=sample_revision
        )
        mock_artifact_repository.get_artifact_by_id = AsyncMock(return_value=sample_artifact)
        mock_artifact_repository.update_artifact_revision_status = AsyncMock()
        mock_artifact_repository.associate_artifact_with_storage = AsyncMock(
            return_value=AssociationArtifactsStoragesData(
                id=uuid.uuid4(),
                artifact_revision_id=sample_revision.id,
                storage_namespace_id=uuid.uuid4(),
            )
        )
        self._setup_reservoir_config(mock_config_provider)
        storage_proxy_client, _ = self._setup_storage_mocks(
            mock_object_storage_repository, mock_storage_namespace_repository, mock_storage_manager
        )

        hf_data = MagicMock()
        hf_data.name = "hf-registry"
        mock_huggingface_repository.get_registry_data_by_artifact_id = AsyncMock(
            return_value=hf_data
        )

        commit_hash_resp = MagicMock()
        commit_hash_resp.commit_hash = "abc123hash"
        storage_proxy_client.get_huggingface_model_commit_hash = AsyncMock(
            return_value=commit_hash_resp
        )

        import_result = MagicMock()
        import_result.task_id = uuid.uuid4()
        storage_proxy_client.import_huggingface_models = AsyncMock(return_value=import_result)

        action = ImportArtifactRevisionAction(artifact_revision_id=sample_revision.id, force=True)
        result = await service.import_revision(action)

        assert result.task_id == import_result.task_id
        mock_artifact_repository.update_artifact_revision_status.assert_any_call(
            sample_revision.id, ArtifactStatus.PULLING
        )

    async def test_failure_sets_status_to_failed_and_reraises(
        self,
        service: ArtifactRevisionService,
        mock_artifact_repository: MagicMock,
        mock_config_provider: MagicMock,
        sample_revision: ArtifactRevisionData,
        sample_artifact: ArtifactData,
    ) -> None:
        """Failure sets status FAILED and re-raises exception"""
        mock_artifact_repository.get_artifact_revision_by_id = AsyncMock(
            return_value=sample_revision
        )
        mock_artifact_repository.get_artifact_by_id = AsyncMock(return_value=sample_artifact)
        mock_artifact_repository.update_artifact_revision_status = AsyncMock()
        mock_config_provider.config.reservoir = None

        action = ImportArtifactRevisionAction(artifact_revision_id=sample_revision.id)

        with pytest.raises(ServerMisconfiguredError):
            await service.import_revision(action)

        mock_artifact_repository.update_artifact_revision_status.assert_called_with(
            sample_revision.id, ArtifactStatus.FAILED
        )

    async def test_unsupported_registry_type_raises_error(
        self,
        service: ArtifactRevisionService,
        mock_artifact_repository: MagicMock,
        mock_object_storage_repository: MagicMock,
        mock_storage_namespace_repository: MagicMock,
        mock_storage_manager: MagicMock,
        mock_config_provider: MagicMock,
    ) -> None:
        """Unsupported registry type raises InvalidArtifactRegistryTypeError"""
        now = datetime.now(UTC)
        revision = ArtifactRevisionData(
            id=uuid.uuid4(),
            artifact_id=uuid.uuid4(),
            version="main",
            readme="",
            size=100,
            status=ArtifactStatus.SCANNED,
            remote_status=None,
            created_at=now,
            updated_at=now,
            digest=None,
            verification_result=None,
        )
        artifact = ArtifactData(
            id=revision.artifact_id,
            name="test-model",
            type=ArtifactType.MODEL,
            description="",
            registry_id=uuid.uuid4(),
            source_registry_id=uuid.uuid4(),
            registry_type="UNKNOWN_TYPE",  # type: ignore[arg-type]
            source_registry_type="UNKNOWN_TYPE",  # type: ignore[arg-type]
            availability=ArtifactAvailability.ALIVE,
            scanned_at=now,
            updated_at=now,
            readonly=True,
            extra=None,
        )

        mock_artifact_repository.get_artifact_revision_by_id = AsyncMock(return_value=revision)
        mock_artifact_repository.get_artifact_by_id = AsyncMock(return_value=artifact)
        mock_artifact_repository.update_artifact_revision_status = AsyncMock()
        self._setup_reservoir_config(mock_config_provider)
        self._setup_storage_mocks(
            mock_object_storage_repository, mock_storage_namespace_repository, mock_storage_manager
        )

        action = ImportArtifactRevisionAction(artifact_revision_id=revision.id)

        with pytest.raises(InvalidArtifactRegistryTypeError):
            await service.import_revision(action)


class TestDelegateImportArtifactRevisionBatchAction:
    """Test cases for DelegateImportArtifactRevisionBatchAction"""

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
    def service(
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

    async def test_leaf_node_calls_local_import(
        self,
        service: ArtifactRevisionService,
        mock_config_provider: MagicMock,
        mock_artifact_registry_repository: MagicMock,
    ) -> None:
        """use_delegation=False (leaf) calls local import_revision"""
        reservoir_cfg = MagicMock()
        reservoir_cfg.use_delegation = False
        mock_config_provider.config.reservoir = reservoir_cfg

        registry_meta = ArtifactRegistryData(
            id=uuid.uuid4(),
            registry_id=uuid.uuid4(),
            name="test-registry",
            type=ArtifactRegistryType.RESERVOIR,
        )
        mock_artifact_registry_repository.get_artifact_registry_data_by_name = AsyncMock(
            return_value=registry_meta
        )

        revision_id = uuid.uuid4()
        revision_data = ArtifactRevisionData(
            id=revision_id,
            artifact_id=uuid.uuid4(),
            version="main",
            readme="",
            size=100,
            status=ArtifactStatus.SCANNED,
            remote_status=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            digest=None,
            verification_result=None,
        )

        import_result = MagicMock()
        import_result.result = revision_data
        import_result.task_id = uuid.uuid4()

        with patch.object(service, "import_revision", new=AsyncMock(return_value=import_result)):
            action = DelegateImportArtifactRevisionBatchAction(
                delegator_reservoir_id=None,
                artifact_type=ArtifactType.MODEL,
                delegatee_target=None,
                artifact_revision_ids=[revision_id],
                force=False,
            )
            result = await service.delegate_import_revision_batch(action)

        assert len(result.result) == 1
        assert result.result[0] == revision_data
        assert len(result.task_ids) == 1

    async def test_delegation_true_calls_remote_reservoir(
        self,
        service: ArtifactRevisionService,
        mock_config_provider: MagicMock,
        mock_artifact_registry_repository: MagicMock,
        mock_reservoir_repository: MagicMock,
        mock_artifact_repository: MagicMock,
    ) -> None:
        """use_delegation=True calls remote ReservoirRegistryClient"""
        reservoir_cfg = MagicMock()
        reservoir_cfg.use_delegation = True
        mock_config_provider.config.reservoir = reservoir_cfg

        registry_id = uuid.uuid4()
        registry_meta = ArtifactRegistryData(
            id=uuid.uuid4(),
            registry_id=registry_id,
            name="reservoir-registry",
            type=ArtifactRegistryType.RESERVOIR,
        )
        mock_artifact_registry_repository.get_artifact_registry_data = AsyncMock(
            return_value=registry_meta
        )

        reservoir_data = MagicMock()
        reservoir_data.name = "reservoir-registry"
        mock_reservoir_repository.get_reservoir_registry_data_by_id = AsyncMock(
            return_value=reservoir_data
        )

        revision_id = uuid.uuid4()
        revision_data = ArtifactRevisionData(
            id=revision_id,
            artifact_id=uuid.uuid4(),
            version="main",
            readme="",
            size=100,
            status=ArtifactStatus.SCANNED,
            remote_status=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            digest=None,
            verification_result=None,
        )
        mock_artifact_repository.get_artifact_revision_by_id = AsyncMock(return_value=revision_data)

        task_id = uuid.uuid4()
        mock_client_resp = MagicMock()
        mock_task = MagicMock()
        mock_task.task_id = str(task_id)
        mock_client_resp.tasks = [mock_task]

        with patch(
            "ai.backend.manager.services.artifact_revision.service.ReservoirRegistryClient"
        ) as MockClient:
            mock_client_instance = MagicMock()
            mock_client_instance.delegate_import_artifacts = AsyncMock(
                return_value=mock_client_resp
            )
            MockClient.return_value = mock_client_instance

            delegator_id = uuid.uuid4()
            action = DelegateImportArtifactRevisionBatchAction(
                delegator_reservoir_id=delegator_id,
                artifact_type=ArtifactType.MODEL,
                delegatee_target=None,
                artifact_revision_ids=[revision_id],
                force=False,
            )
            result = await service.delegate_import_revision_batch(action)

        assert len(result.result) == 1
        assert result.task_ids == [task_id]

    async def test_non_reservoir_raises_bad_request(
        self,
        service: ArtifactRevisionService,
        mock_config_provider: MagicMock,
        mock_artifact_registry_repository: MagicMock,
    ) -> None:
        """non-Reservoir type raises ArtifactImportBadRequestError"""
        reservoir_cfg = MagicMock()
        reservoir_cfg.use_delegation = True
        mock_config_provider.config.reservoir = reservoir_cfg

        registry_meta = ArtifactRegistryData(
            id=uuid.uuid4(),
            registry_id=uuid.uuid4(),
            name="hf-registry",
            type=ArtifactRegistryType.HUGGINGFACE,
        )
        mock_artifact_registry_repository.get_artifact_registry_data = AsyncMock(
            return_value=registry_meta
        )

        action = DelegateImportArtifactRevisionBatchAction(
            delegator_reservoir_id=uuid.uuid4(),
            artifact_type=ArtifactType.MODEL,
            delegatee_target=None,
            artifact_revision_ids=[uuid.uuid4()],
            force=False,
        )

        with pytest.raises(ArtifactImportBadRequestError):
            await service.delegate_import_revision_batch(action)

    async def test_none_task_id_preserved(
        self,
        service: ArtifactRevisionService,
        mock_config_provider: MagicMock,
        mock_artifact_registry_repository: MagicMock,
    ) -> None:
        """None task_id preserved in result"""
        reservoir_cfg = MagicMock()
        reservoir_cfg.use_delegation = False
        mock_config_provider.config.reservoir = reservoir_cfg

        registry_meta = ArtifactRegistryData(
            id=uuid.uuid4(),
            registry_id=uuid.uuid4(),
            name="test-registry",
            type=ArtifactRegistryType.RESERVOIR,
        )
        mock_artifact_registry_repository.get_artifact_registry_data_by_name = AsyncMock(
            return_value=registry_meta
        )

        revision_data = ArtifactRevisionData(
            id=uuid.uuid4(),
            artifact_id=uuid.uuid4(),
            version="main",
            readme="",
            size=100,
            status=ArtifactStatus.SCANNED,
            remote_status=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            digest=None,
            verification_result=None,
        )

        import_result = MagicMock()
        import_result.result = revision_data
        import_result.task_id = None

        with patch.object(service, "import_revision", new=AsyncMock(return_value=import_result)):
            action = DelegateImportArtifactRevisionBatchAction(
                delegator_reservoir_id=None,
                artifact_type=ArtifactType.MODEL,
                delegatee_target=None,
                artifact_revision_ids=[revision_data.id],
                force=False,
            )
            result = await service.delegate_import_revision_batch(action)

        assert result.task_ids == [None]


class TestCancelImportAction:
    """Test cases for CancelImportAction"""

    @pytest.fixture
    def mock_artifact_repository(self) -> MagicMock:
        return MagicMock(spec=ArtifactRepository)

    @pytest.fixture
    def service(self, mock_artifact_repository: MagicMock) -> ArtifactRevisionService:
        return ArtifactRevisionService(
            artifact_repository=mock_artifact_repository,
            artifact_registry_repository=MagicMock(spec=ArtifactRegistryRepository),
            object_storage_repository=MagicMock(spec=ObjectStorageRepository),
            vfs_storage_repository=MagicMock(spec=VFSStorageRepository),
            storage_namespace_repository=MagicMock(spec=StorageNamespaceRepository),
            huggingface_registry_repository=MagicMock(spec=HuggingFaceRepository),
            reservoir_registry_repository=MagicMock(spec=ReservoirRegistryRepository),
            vfolder_repository=MagicMock(spec=VfolderRepository),
            storage_manager=MagicMock(),
            config_provider=MagicMock(),
            valkey_artifact_client=MagicMock(),
            background_task_manager=MagicMock(),
        )

    async def test_pulling_state_resets_and_returns_data(
        self,
        service: ArtifactRevisionService,
        mock_artifact_repository: MagicMock,
    ) -> None:
        """PULLING state resets + returns revision data"""
        now = datetime.now(UTC)
        revision_id = uuid.uuid4()
        reset_revision = ArtifactRevisionData(
            id=revision_id,
            artifact_id=uuid.uuid4(),
            version="main",
            readme="",
            size=100,
            status=ArtifactStatus.SCANNED,
            remote_status=None,
            created_at=now,
            updated_at=now,
            digest=None,
            verification_result=None,
        )

        mock_artifact_repository.reset_artifact_revision_status = AsyncMock()
        mock_artifact_repository.get_artifact_revision_by_id = AsyncMock(
            return_value=reset_revision
        )

        action = CancelImportAction(artifact_revision_id=revision_id)
        result = await service.cancel_import(action)

        assert result.result == reset_revision
        mock_artifact_repository.reset_artifact_revision_status.assert_called_once_with(revision_id)

    async def test_available_state_still_resets(
        self,
        service: ArtifactRevisionService,
        mock_artifact_repository: MagicMock,
    ) -> None:
        """AVAILABLE state also calls reset (service doesn't check state)"""
        now = datetime.now(UTC)
        revision_id = uuid.uuid4()
        revision = ArtifactRevisionData(
            id=revision_id,
            artifact_id=uuid.uuid4(),
            version="main",
            readme="",
            size=100,
            status=ArtifactStatus.AVAILABLE,
            remote_status=None,
            created_at=now,
            updated_at=now,
            digest=None,
            verification_result=None,
        )

        mock_artifact_repository.reset_artifact_revision_status = AsyncMock()
        mock_artifact_repository.get_artifact_revision_by_id = AsyncMock(return_value=revision)

        action = CancelImportAction(artifact_revision_id=revision_id)
        result = await service.cancel_import(action)

        assert result.result == revision
        mock_artifact_repository.reset_artifact_revision_status.assert_called_once_with(revision_id)


class TestAssociateWithStorageAction:
    """Test cases for AssociateWithStorageAction"""

    @pytest.fixture
    def mock_artifact_repository(self) -> MagicMock:
        return MagicMock(spec=ArtifactRepository)

    @pytest.fixture
    def service(self, mock_artifact_repository: MagicMock) -> ArtifactRevisionService:
        return ArtifactRevisionService(
            artifact_repository=mock_artifact_repository,
            artifact_registry_repository=MagicMock(spec=ArtifactRegistryRepository),
            object_storage_repository=MagicMock(spec=ObjectStorageRepository),
            vfs_storage_repository=MagicMock(spec=VFSStorageRepository),
            storage_namespace_repository=MagicMock(spec=StorageNamespaceRepository),
            huggingface_registry_repository=MagicMock(spec=HuggingFaceRepository),
            reservoir_registry_repository=MagicMock(spec=ReservoirRegistryRepository),
            vfolder_repository=MagicMock(spec=VfolderRepository),
            storage_manager=MagicMock(),
            config_provider=MagicMock(),
            valkey_artifact_client=MagicMock(),
            background_task_manager=MagicMock(),
        )

    async def test_object_storage_association(
        self,
        service: ArtifactRevisionService,
        mock_artifact_repository: MagicMock,
    ) -> None:
        """OBJECT_STORAGE type association record created"""
        revision_id = uuid.uuid4()
        namespace_id = uuid.uuid4()
        association = AssociationArtifactsStoragesData(
            id=uuid.uuid4(),
            artifact_revision_id=revision_id,
            storage_namespace_id=namespace_id,
        )
        mock_artifact_repository.associate_artifact_with_storage = AsyncMock(
            return_value=association
        )

        action = AssociateWithStorageAction(
            artifact_revision_id=revision_id,
            storage_namespace_id=namespace_id,
            storage_type=ArtifactStorageType.OBJECT_STORAGE,
        )
        result = await service.associate_with_storage(action)

        assert result.result == association
        mock_artifact_repository.associate_artifact_with_storage.assert_called_once_with(
            revision_id, namespace_id, ArtifactStorageType.OBJECT_STORAGE
        )

    async def test_vfs_storage_association(
        self,
        service: ArtifactRevisionService,
        mock_artifact_repository: MagicMock,
    ) -> None:
        """VFS_STORAGE type association record created"""
        revision_id = uuid.uuid4()
        namespace_id = uuid.uuid4()
        association = AssociationArtifactsStoragesData(
            id=uuid.uuid4(),
            artifact_revision_id=revision_id,
            storage_namespace_id=namespace_id,
        )
        mock_artifact_repository.associate_artifact_with_storage = AsyncMock(
            return_value=association
        )

        action = AssociateWithStorageAction(
            artifact_revision_id=revision_id,
            storage_namespace_id=namespace_id,
            storage_type=ArtifactStorageType.VFS_STORAGE,
        )
        result = await service.associate_with_storage(action)

        assert result.result == association
        mock_artifact_repository.associate_artifact_with_storage.assert_called_once_with(
            revision_id, namespace_id, ArtifactStorageType.VFS_STORAGE
        )


class TestDisassociateWithStorageAction:
    """Test cases for DisassociateWithStorageAction"""

    @pytest.fixture
    def mock_artifact_repository(self) -> MagicMock:
        return MagicMock(spec=ArtifactRepository)

    @pytest.fixture
    def service(self, mock_artifact_repository: MagicMock) -> ArtifactRevisionService:
        return ArtifactRevisionService(
            artifact_repository=mock_artifact_repository,
            artifact_registry_repository=MagicMock(spec=ArtifactRegistryRepository),
            object_storage_repository=MagicMock(spec=ObjectStorageRepository),
            vfs_storage_repository=MagicMock(spec=VFSStorageRepository),
            storage_namespace_repository=MagicMock(spec=StorageNamespaceRepository),
            huggingface_registry_repository=MagicMock(spec=HuggingFaceRepository),
            reservoir_registry_repository=MagicMock(spec=ReservoirRegistryRepository),
            vfolder_repository=MagicMock(spec=VfolderRepository),
            storage_manager=MagicMock(),
            config_provider=MagicMock(),
            valkey_artifact_client=MagicMock(),
            background_task_manager=MagicMock(),
        )

    async def test_disassociation_record_deleted(
        self,
        service: ArtifactRevisionService,
        mock_artifact_repository: MagicMock,
    ) -> None:
        """Association record deleted"""
        revision_id = uuid.uuid4()
        namespace_id = uuid.uuid4()
        association = AssociationArtifactsStoragesData(
            id=uuid.uuid4(),
            artifact_revision_id=revision_id,
            storage_namespace_id=namespace_id,
        )
        mock_artifact_repository.disassociate_artifact_with_storage = AsyncMock(
            return_value=association
        )

        action = DisassociateWithStorageAction(
            artifact_revision_id=revision_id,
            storage_namespace_id=namespace_id,
        )
        result = await service.disassociate_with_storage(action)

        assert result.result == association
        mock_artifact_repository.disassociate_artifact_with_storage.assert_called_once_with(
            revision_id, namespace_id
        )


class TestCleanupArtifactRevisionAction:
    """Test cases for CleanupArtifactRevisionAction"""

    @pytest.fixture
    def mock_artifact_repository(self) -> MagicMock:
        return MagicMock(spec=ArtifactRepository)

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
    def mock_storage_manager(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def mock_config_provider(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def service(
        self,
        mock_artifact_repository: MagicMock,
        mock_object_storage_repository: MagicMock,
        mock_vfs_storage_repository: MagicMock,
        mock_storage_namespace_repository: MagicMock,
        mock_storage_manager: MagicMock,
        mock_config_provider: MagicMock,
    ) -> ArtifactRevisionService:
        return ArtifactRevisionService(
            artifact_repository=mock_artifact_repository,
            artifact_registry_repository=MagicMock(spec=ArtifactRegistryRepository),
            object_storage_repository=mock_object_storage_repository,
            vfs_storage_repository=mock_vfs_storage_repository,
            storage_namespace_repository=mock_storage_namespace_repository,
            huggingface_registry_repository=MagicMock(spec=HuggingFaceRepository),
            reservoir_registry_repository=MagicMock(spec=ReservoirRegistryRepository),
            vfolder_repository=MagicMock(spec=VfolderRepository),
            storage_manager=mock_storage_manager,
            config_provider=mock_config_provider,
            valkey_artifact_client=MagicMock(),
            background_task_manager=MagicMock(),
        )

    async def test_available_state_deletes_and_disassociates(
        self,
        service: ArtifactRevisionService,
        mock_artifact_repository: MagicMock,
        mock_object_storage_repository: MagicMock,
        mock_storage_namespace_repository: MagicMock,
        mock_storage_manager: MagicMock,
        mock_config_provider: MagicMock,
    ) -> None:
        """AVAILABLE state deletes S3 objects + disassociates"""
        now = datetime.now(UTC)
        revision_id = uuid.uuid4()
        artifact_id = uuid.uuid4()
        namespace_id = uuid.uuid4()

        revision = ArtifactRevisionData(
            id=revision_id,
            artifact_id=artifact_id,
            version="v1",
            readme="",
            size=100,
            status=ArtifactStatus.AVAILABLE,
            remote_status=None,
            created_at=now,
            updated_at=now,
            digest=None,
            verification_result=None,
        )
        artifact = ArtifactData(
            id=artifact_id,
            name="test-model",
            type=ArtifactType.MODEL,
            description="",
            registry_id=uuid.uuid4(),
            source_registry_id=uuid.uuid4(),
            registry_type=ArtifactRegistryType.RESERVOIR,
            source_registry_type=ArtifactRegistryType.RESERVOIR,
            availability=ArtifactAvailability.ALIVE,
            scanned_at=now,
            updated_at=now,
            readonly=True,
            extra=None,
        )

        mock_artifact_repository.get_artifact_revision_by_id = AsyncMock(
            side_effect=[revision, revision]
        )
        mock_artifact_repository.get_artifact_by_id = AsyncMock(return_value=artifact)
        mock_artifact_repository.reset_artifact_revision_status = AsyncMock()
        mock_artifact_repository.disassociate_artifact_with_storage = AsyncMock(
            return_value=AssociationArtifactsStoragesData(
                id=uuid.uuid4(),
                artifact_revision_id=revision_id,
                storage_namespace_id=namespace_id,
            )
        )

        reservoir_cfg = MagicMock()
        reservoir_cfg.archive_storage = "test-storage"
        reservoir_cfg.config.storage_type = ArtifactStorageType.OBJECT_STORAGE.value
        reservoir_cfg.config.bucket_name = "test-bucket"
        mock_config_provider.config.reservoir = reservoir_cfg

        storage_data = MagicMock()
        storage_data.id = uuid.uuid4()
        storage_data.host = "storage-host"
        storage_data.name = "test-storage"
        mock_object_storage_repository.get_by_name = AsyncMock(return_value=storage_data)

        namespace_data = MagicMock()
        namespace_data.id = namespace_id
        namespace_data.namespace = "test-bucket"
        mock_storage_namespace_repository.get_by_storage_and_namespace = AsyncMock(
            return_value=namespace_data
        )

        storage_proxy_client = MagicMock()
        storage_proxy_client.delete_s3_object = AsyncMock()
        mock_storage_manager.get_manager_facing_client.return_value = storage_proxy_client

        action = CleanupArtifactRevisionAction(artifact_revision_id=revision_id)
        result = await service.cleanup(action)

        assert result.result == revision
        storage_proxy_client.delete_s3_object.assert_called_once()
        mock_artifact_repository.disassociate_artifact_with_storage.assert_called_once()

    async def test_scanned_state_raises_bad_request(
        self,
        service: ArtifactRevisionService,
        mock_artifact_repository: MagicMock,
    ) -> None:
        """SCANNED state raises ArtifactDeletionBadRequestError"""
        now = datetime.now(UTC)
        revision = ArtifactRevisionData(
            id=uuid.uuid4(),
            artifact_id=uuid.uuid4(),
            version="v1",
            readme="",
            size=100,
            status=ArtifactStatus.SCANNED,
            remote_status=None,
            created_at=now,
            updated_at=now,
            digest=None,
            verification_result=None,
        )
        mock_artifact_repository.get_artifact_revision_by_id = AsyncMock(return_value=revision)

        action = CleanupArtifactRevisionAction(artifact_revision_id=revision.id)

        with pytest.raises(ArtifactDeletionBadRequestError):
            await service.cleanup(action)

    async def test_pulling_state_raises_bad_request(
        self,
        service: ArtifactRevisionService,
        mock_artifact_repository: MagicMock,
    ) -> None:
        """PULLING state raises ArtifactDeletionBadRequestError"""
        now = datetime.now(UTC)
        revision = ArtifactRevisionData(
            id=uuid.uuid4(),
            artifact_id=uuid.uuid4(),
            version="v1",
            readme="",
            size=100,
            status=ArtifactStatus.PULLING,
            remote_status=None,
            created_at=now,
            updated_at=now,
            digest=None,
            verification_result=None,
        )
        mock_artifact_repository.get_artifact_revision_by_id = AsyncMock(return_value=revision)

        action = CleanupArtifactRevisionAction(artifact_revision_id=revision.id)

        with pytest.raises(ArtifactDeletionBadRequestError):
            await service.cleanup(action)

    async def test_vfs_storage_fallback(
        self,
        service: ArtifactRevisionService,
        mock_artifact_repository: MagicMock,
        mock_object_storage_repository: MagicMock,
        mock_vfs_storage_repository: MagicMock,
        mock_storage_namespace_repository: MagicMock,
        mock_storage_manager: MagicMock,
        mock_config_provider: MagicMock,
    ) -> None:
        """tries object_storage first then vfs_storage fallback"""
        now = datetime.now(UTC)
        revision_id = uuid.uuid4()
        artifact_id = uuid.uuid4()
        namespace_id = uuid.uuid4()

        revision = ArtifactRevisionData(
            id=revision_id,
            artifact_id=artifact_id,
            version="v1",
            readme="",
            size=100,
            status=ArtifactStatus.AVAILABLE,
            remote_status=None,
            created_at=now,
            updated_at=now,
            digest=None,
            verification_result=None,
        )
        artifact = ArtifactData(
            id=artifact_id,
            name="test-model",
            type=ArtifactType.MODEL,
            description="",
            registry_id=uuid.uuid4(),
            source_registry_id=uuid.uuid4(),
            registry_type=ArtifactRegistryType.RESERVOIR,
            source_registry_type=ArtifactRegistryType.RESERVOIR,
            availability=ArtifactAvailability.ALIVE,
            scanned_at=now,
            updated_at=now,
            readonly=True,
            extra=None,
        )

        mock_artifact_repository.get_artifact_revision_by_id = AsyncMock(
            side_effect=[revision, revision]
        )
        mock_artifact_repository.get_artifact_by_id = AsyncMock(return_value=artifact)
        mock_artifact_repository.reset_artifact_revision_status = AsyncMock()
        mock_artifact_repository.disassociate_artifact_with_storage = AsyncMock(
            return_value=AssociationArtifactsStoragesData(
                id=uuid.uuid4(),
                artifact_revision_id=revision_id,
                storage_namespace_id=namespace_id,
            )
        )

        reservoir_cfg = MagicMock()
        reservoir_cfg.archive_storage = "test-storage"
        reservoir_cfg.config.storage_type = ArtifactStorageType.VFS_STORAGE.value
        reservoir_cfg.config.subpath = "test-subpath"
        mock_config_provider.config.reservoir = reservoir_cfg

        mock_object_storage_repository.get_by_name = AsyncMock(side_effect=Exception("not found"))

        vfs_data = MagicMock()
        vfs_data.id = uuid.uuid4()
        vfs_data.host = "vfs-host"
        vfs_data.name = "test-storage"
        mock_vfs_storage_repository.get_by_name = AsyncMock(return_value=vfs_data)

        namespace_data = MagicMock()
        namespace_data.id = namespace_id
        namespace_data.namespace = "test-subpath"
        mock_storage_namespace_repository.get_by_storage_and_namespace = AsyncMock(
            return_value=namespace_data
        )

        storage_proxy_client = MagicMock()
        storage_proxy_client.delete_s3_object = AsyncMock()
        mock_storage_manager.get_manager_facing_client.return_value = storage_proxy_client

        action = CleanupArtifactRevisionAction(artifact_revision_id=revision_id)
        result = await service.cleanup(action)

        assert result.result == revision
        mock_vfs_storage_repository.get_by_name.assert_called_once()


class TestGetDownloadProgressAction:
    """Test cases for GetDownloadProgressAction"""

    @pytest.fixture
    def mock_artifact_repository(self) -> MagicMock:
        return MagicMock(spec=ArtifactRepository)

    @pytest.fixture
    def mock_valkey_artifact_client(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def mock_config_provider(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def mock_reservoir_repository(self) -> MagicMock:
        return MagicMock(spec=ReservoirRegistryRepository)

    @pytest.fixture
    def service(
        self,
        mock_artifact_repository: MagicMock,
        mock_valkey_artifact_client: MagicMock,
        mock_config_provider: MagicMock,
        mock_reservoir_repository: MagicMock,
    ) -> ArtifactRevisionService:
        return ArtifactRevisionService(
            artifact_repository=mock_artifact_repository,
            artifact_registry_repository=MagicMock(spec=ArtifactRegistryRepository),
            object_storage_repository=MagicMock(spec=ObjectStorageRepository),
            vfs_storage_repository=MagicMock(spec=VFSStorageRepository),
            storage_namespace_repository=MagicMock(spec=StorageNamespaceRepository),
            huggingface_registry_repository=MagicMock(spec=HuggingFaceRepository),
            reservoir_registry_repository=mock_reservoir_repository,
            vfolder_repository=MagicMock(spec=VfolderRepository),
            storage_manager=MagicMock(),
            config_provider=mock_config_provider,
            valkey_artifact_client=mock_valkey_artifact_client,
            background_task_manager=MagicMock(),
        )

    async def test_huggingface_returns_local_only(
        self,
        service: ArtifactRevisionService,
        mock_artifact_repository: MagicMock,
        mock_valkey_artifact_client: MagicMock,
    ) -> None:
        """HuggingFace returns local progress only (remote=None)"""
        now = datetime.now(UTC)
        revision = ArtifactRevisionData(
            id=uuid.uuid4(),
            artifact_id=uuid.uuid4(),
            version="main",
            readme="",
            size=100,
            status=ArtifactStatus.PULLING,
            remote_status=None,
            created_at=now,
            updated_at=now,
            digest=None,
            verification_result=None,
        )
        artifact = ArtifactData(
            id=revision.artifact_id,
            name="test-model",
            type=ArtifactType.MODEL,
            description="",
            registry_id=uuid.uuid4(),
            source_registry_id=uuid.uuid4(),
            registry_type=ArtifactRegistryType.HUGGINGFACE,
            source_registry_type=ArtifactRegistryType.HUGGINGFACE,
            availability=ArtifactAvailability.ALIVE,
            scanned_at=now,
            updated_at=now,
            readonly=True,
            extra=None,
        )

        mock_artifact_repository.get_artifact_revision_by_id = AsyncMock(return_value=revision)
        mock_artifact_repository.get_artifact_by_id = AsyncMock(return_value=artifact)

        local_progress = MagicMock()
        local_progress.artifact_progress = None
        mock_valkey_artifact_client.get_download_progress = AsyncMock(return_value=local_progress)

        action = GetDownloadProgressAction(artifact_revision_id=revision.id)
        result = await service.get_download_progress(action)

        assert result.download_progress.local is not None
        assert result.download_progress.remote is None

    async def test_reservoir_delegation_returns_local_and_remote(
        self,
        service: ArtifactRevisionService,
        mock_artifact_repository: MagicMock,
        mock_valkey_artifact_client: MagicMock,
        mock_config_provider: MagicMock,
        mock_reservoir_repository: MagicMock,
    ) -> None:
        """Reservoir+delegation returns local+remote progress"""
        now = datetime.now(UTC)
        revision = ArtifactRevisionData(
            id=uuid.uuid4(),
            artifact_id=uuid.uuid4(),
            version="main",
            readme="",
            size=100,
            status=ArtifactStatus.SCANNED,
            remote_status=ArtifactRemoteStatus.AVAILABLE,
            created_at=now,
            updated_at=now,
            digest=None,
            verification_result=None,
        )
        artifact = ArtifactData(
            id=revision.artifact_id,
            name="test-model",
            type=ArtifactType.MODEL,
            description="",
            registry_id=uuid.uuid4(),
            source_registry_id=uuid.uuid4(),
            registry_type=ArtifactRegistryType.RESERVOIR,
            source_registry_type=ArtifactRegistryType.RESERVOIR,
            availability=ArtifactAvailability.ALIVE,
            scanned_at=now,
            updated_at=now,
            readonly=True,
            extra=None,
        )

        mock_artifact_repository.get_artifact_revision_by_id = AsyncMock(return_value=revision)
        mock_artifact_repository.get_artifact_by_id = AsyncMock(return_value=artifact)

        local_progress = MagicMock()
        local_progress.artifact_progress = None
        mock_valkey_artifact_client.get_download_progress = AsyncMock(return_value=local_progress)

        reservoir_cfg = MagicMock()
        reservoir_cfg.use_delegation = True
        mock_config_provider.config.reservoir = reservoir_cfg

        registry_data = MagicMock()
        mock_reservoir_repository.get_reservoir_registry_data_by_id = AsyncMock(
            return_value=registry_data
        )

        remote_local_progress = ArtifactRevisionDownloadProgress(
            progress=None,
            status=ArtifactStatus.AVAILABLE.value,
        )
        remote_resp = MagicMock()
        remote_resp.download_progress.local = remote_local_progress

        with patch(
            "ai.backend.manager.services.artifact_revision.service.ReservoirRegistryClient"
        ) as MockClient:
            mock_client = MagicMock()
            mock_client.get_download_progress = AsyncMock(return_value=remote_resp)
            MockClient.return_value = mock_client

            action = GetDownloadProgressAction(artifact_revision_id=revision.id)
            result = await service.get_download_progress(action)

        assert result.download_progress.local is not None
        assert result.download_progress.remote is not None
        assert result.download_progress.remote.status == ArtifactStatus.AVAILABLE.value

    async def test_remote_query_failure_logs_warning(
        self,
        service: ArtifactRevisionService,
        mock_artifact_repository: MagicMock,
        mock_valkey_artifact_client: MagicMock,
        mock_config_provider: MagicMock,
        mock_reservoir_repository: MagicMock,
    ) -> None:
        """Remote query failure logs warning + returns without progress"""
        now = datetime.now(UTC)
        revision = ArtifactRevisionData(
            id=uuid.uuid4(),
            artifact_id=uuid.uuid4(),
            version="main",
            readme="",
            size=100,
            status=ArtifactStatus.SCANNED,
            remote_status=ArtifactRemoteStatus.SCANNED,
            created_at=now,
            updated_at=now,
            digest=None,
            verification_result=None,
        )
        artifact = ArtifactData(
            id=revision.artifact_id,
            name="test-model",
            type=ArtifactType.MODEL,
            description="",
            registry_id=uuid.uuid4(),
            source_registry_id=uuid.uuid4(),
            registry_type=ArtifactRegistryType.RESERVOIR,
            source_registry_type=ArtifactRegistryType.RESERVOIR,
            availability=ArtifactAvailability.ALIVE,
            scanned_at=now,
            updated_at=now,
            readonly=True,
            extra=None,
        )

        mock_artifact_repository.get_artifact_revision_by_id = AsyncMock(return_value=revision)
        mock_artifact_repository.get_artifact_by_id = AsyncMock(return_value=artifact)

        local_progress = MagicMock()
        local_progress.artifact_progress = None
        mock_valkey_artifact_client.get_download_progress = AsyncMock(return_value=local_progress)

        reservoir_cfg = MagicMock()
        reservoir_cfg.use_delegation = True
        mock_config_provider.config.reservoir = reservoir_cfg

        mock_reservoir_repository.get_reservoir_registry_data_by_id = AsyncMock(
            side_effect=Exception("connection error")
        )

        action = GetDownloadProgressAction(artifact_revision_id=revision.id)
        result = await service.get_download_progress(action)

        assert result.download_progress.remote is not None
        assert result.download_progress.remote.progress is None
        assert result.download_progress.remote.status == ArtifactRemoteStatus.SCANNED.value
