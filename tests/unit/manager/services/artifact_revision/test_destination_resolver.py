"""
Tests for ArtifactImportDestinationResolver functionality.
Tests the destination resolution logic for artifact imports.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.storage.types import ArtifactStorageImportStep, ArtifactStorageType
from ai.backend.common.types import QuotaScopeID, QuotaScopeType, VFolderID
from ai.backend.manager.config.unified import (
    ReservoirConfig,
    ReservoirObjectStorageConfig,
    ReservoirVFolderStorageConfig,
    ReservoirVFSStorageConfig,
)
from ai.backend.manager.data.vfolder.types import (
    VFolderData,
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderUsageMode,
)
from ai.backend.manager.errors.storage import (
    UnsupportedStorageTypeError,
    VFolderNotFound,
    VFolderStorageNamespaceNotResolvableError,
)
from ai.backend.manager.repositories.object_storage.repository import ObjectStorageRepository
from ai.backend.manager.repositories.storage_namespace.repository import StorageNamespaceRepository
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.repositories.vfs_storage.repository import VFSStorageRepository
from ai.backend.manager.services.artifact_revision.destination_resolver import (
    ArtifactImportDestinationResolver,
    ImportDestinationInfo,
)


class TestArtifactImportDestinationResolver:
    """Test cases for ArtifactImportDestinationResolver"""

    @pytest.fixture
    def mock_vfolder_repository(self) -> MagicMock:
        """Create mocked VfolderRepository"""
        return MagicMock(spec=VfolderRepository)

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
    def destination_resolver(
        self,
        mock_vfolder_repository: MagicMock,
        mock_object_storage_repository: MagicMock,
        mock_vfs_storage_repository: MagicMock,
        mock_storage_namespace_repository: MagicMock,
    ) -> ArtifactImportDestinationResolver:
        """Create ArtifactImportDestinationResolver instance with mocked repositories"""
        return ArtifactImportDestinationResolver(
            vfolder_repository=mock_vfolder_repository,
            object_storage_repository=mock_object_storage_repository,
            vfs_storage_repository=mock_vfs_storage_repository,
            storage_namespace_repository=mock_storage_namespace_repository,
        )

    @pytest.fixture
    def sample_vfolder_id(self) -> uuid.UUID:
        """Create sample vfolder ID"""
        return uuid.uuid4()

    @pytest.fixture
    def sample_quota_scope_id(self) -> QuotaScopeID:
        """Create sample quota scope ID"""
        return QuotaScopeID(QuotaScopeType.USER, uuid.uuid4())

    @pytest.fixture
    def sample_vfolder_data(
        self, sample_vfolder_id: uuid.UUID, sample_quota_scope_id: QuotaScopeID
    ) -> VFolderData:
        """Create sample VFolderData"""
        now = datetime.now(UTC)
        return VFolderData(
            id=sample_vfolder_id,
            name="test-vfolder",
            host="test-proxy:test-volume",
            domain_name="default",
            quota_scope_id=sample_quota_scope_id,
            usage_mode=VFolderUsageMode.GENERAL,
            permission=None,
            max_files=1000,
            max_size=1024 * 1024 * 1024,
            num_files=0,
            cur_size=0,
            created_at=now,
            last_used=None,
            creator=None,
            unmanaged_path=None,
            cloneable=False,
            status=VFolderOperationStatus.READY,
            user=None,
            group=None,
            ownership_type=VFolderOwnershipType.USER,
        )

    @pytest.fixture
    def sample_object_storage_config(self) -> ReservoirObjectStorageConfig:
        """Create sample ReservoirObjectStorageConfig"""
        return ReservoirObjectStorageConfig(
            storage_type=ArtifactStorageType.OBJECT_STORAGE.value,
            bucket_name="test-bucket",
        )

    @pytest.fixture
    def sample_vfs_storage_config(self) -> ReservoirVFSStorageConfig:
        """Create sample ReservoirVFSStorageConfig"""
        return ReservoirVFSStorageConfig(
            storage_type=ArtifactStorageType.VFS_STORAGE.value,
            subpath="test-subpath",
        )

    @pytest.fixture
    def sample_vfolder_storage_config(self) -> ReservoirVFolderStorageConfig:
        """Create sample ReservoirVFolderStorageConfig"""
        return ReservoirVFolderStorageConfig(
            storage_type=ArtifactStorageType.VFOLDER_STORAGE.value,
        )

    @pytest.fixture
    def sample_reservoir_config_object_storage(
        self, sample_object_storage_config: ReservoirObjectStorageConfig
    ) -> ReservoirConfig:
        """Create sample ReservoirConfig with object storage"""
        mock_config = MagicMock(spec=ReservoirConfig)
        mock_config.config = sample_object_storage_config
        mock_config.archive_storage = "test-archive-storage"
        mock_config.resolve_storage_step_selection.return_value = {
            ArtifactStorageImportStep.DOWNLOAD: "download-volume",
            ArtifactStorageImportStep.VERIFY: "verify-volume",
            ArtifactStorageImportStep.ARCHIVE: "archive-volume",
        }
        return mock_config

    @pytest.fixture
    def sample_reservoir_config_vfs_storage(
        self, sample_vfs_storage_config: ReservoirVFSStorageConfig
    ) -> ReservoirConfig:
        """Create sample ReservoirConfig with VFS storage"""
        mock_config = MagicMock(spec=ReservoirConfig)
        mock_config.config = sample_vfs_storage_config
        mock_config.archive_storage = "test-vfs-storage"
        mock_config.resolve_storage_step_selection.return_value = {
            ArtifactStorageImportStep.DOWNLOAD: "vfs-download",
            ArtifactStorageImportStep.VERIFY: "vfs-verify",
            ArtifactStorageImportStep.ARCHIVE: "vfs-archive",
        }
        return mock_config

    @pytest.fixture
    def sample_reservoir_config_vfolder_storage(
        self, sample_vfolder_storage_config: ReservoirVFolderStorageConfig
    ) -> ReservoirConfig:
        """Create sample ReservoirConfig with VFolder storage"""
        mock_config = MagicMock(spec=ReservoirConfig)
        mock_config.config = sample_vfolder_storage_config
        return mock_config

    async def test_resolve_with_vfolder_id(
        self,
        destination_resolver: ArtifactImportDestinationResolver,
        mock_vfolder_repository: MagicMock,
        sample_vfolder_id: uuid.UUID,
        sample_vfolder_data: VFolderData,
        sample_reservoir_config_object_storage: ReservoirConfig,
    ) -> None:
        """Test resolve() routes to vfolder destination when vfolder_id is provided"""
        mock_vfolder_repository.get_by_id = AsyncMock(return_value=sample_vfolder_data)

        result = await destination_resolver.resolve(
            sample_reservoir_config_object_storage,
            sample_vfolder_id,
        )

        assert result.storage_host == "test-proxy"
        assert result.vfid is not None
        assert result.vfid.folder_id == sample_vfolder_data.id
        assert result.storage_type is None
        assert result.namespace_id is None
        mock_vfolder_repository.get_by_id.assert_called_once_with(sample_vfolder_id)

    async def test_resolve_without_vfolder_id(
        self,
        destination_resolver: ArtifactImportDestinationResolver,
        mock_object_storage_repository: MagicMock,
        mock_storage_namespace_repository: MagicMock,
        sample_reservoir_config_object_storage: ReservoirConfig,
    ) -> None:
        """Test resolve() routes to storage destination when vfolder_id is not provided"""
        storage_id = uuid.uuid4()
        namespace_id = uuid.uuid4()

        mock_storage_data = MagicMock()
        mock_storage_data.id = storage_id
        mock_storage_data.host = "storage-host"
        mock_storage_data.name = "test-storage"
        mock_object_storage_repository.get_by_name = AsyncMock(return_value=mock_storage_data)

        mock_namespace_data = MagicMock()
        mock_namespace_data.id = namespace_id
        mock_storage_namespace_repository.get_by_storage_and_namespace = AsyncMock(
            return_value=mock_namespace_data
        )

        result = await destination_resolver.resolve(
            sample_reservoir_config_object_storage,
        )

        assert result.storage_host == "storage-host"
        assert result.vfid is None
        assert result.storage_type == ArtifactStorageType.OBJECT_STORAGE.value
        assert result.namespace_id == namespace_id

    async def test_resolve_vfolder_destination_success(
        self,
        destination_resolver: ArtifactImportDestinationResolver,
        mock_vfolder_repository: MagicMock,
        sample_vfolder_id: uuid.UUID,
        sample_vfolder_data: VFolderData,
        sample_quota_scope_id: QuotaScopeID,
    ) -> None:
        """Test _resolve_vfolder_destination returns correct ImportDestinationInfo"""
        mock_vfolder_repository.get_by_id = AsyncMock(return_value=sample_vfolder_data)

        result = await destination_resolver._resolve_vfolder_destination(sample_vfolder_id)

        assert isinstance(result, ImportDestinationInfo)
        assert result.storage_host == "test-proxy"
        assert result.vfid == VFolderID(sample_quota_scope_id, sample_vfolder_id)
        assert result.storage_type is None
        assert result.namespace_id is None

        # Verify storage_step_mappings uses volume name for all steps
        assert result.storage_step_mappings[ArtifactStorageImportStep.DOWNLOAD] == "test-volume"
        assert result.storage_step_mappings[ArtifactStorageImportStep.VERIFY] == "test-volume"
        assert result.storage_step_mappings[ArtifactStorageImportStep.ARCHIVE] == "test-volume"

    async def test_resolve_vfolder_destination_not_found(
        self,
        destination_resolver: ArtifactImportDestinationResolver,
        mock_vfolder_repository: MagicMock,
        sample_vfolder_id: uuid.UUID,
    ) -> None:
        """Test _resolve_vfolder_destination raises VFolderNotFound when vfolder doesn't exist"""
        mock_vfolder_repository.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(VFolderNotFound):
            await destination_resolver._resolve_vfolder_destination(sample_vfolder_id)

    def test_resolve_storage_namespace_object_storage(
        self,
        destination_resolver: ArtifactImportDestinationResolver,
        sample_reservoir_config_object_storage: ReservoirConfig,
    ) -> None:
        """Test resolve_storage_namespace returns bucket_name for object storage"""
        result = destination_resolver.resolve_storage_namespace(
            sample_reservoir_config_object_storage
        )

        assert result == "test-bucket"

    def test_resolve_storage_namespace_vfs_storage(
        self,
        destination_resolver: ArtifactImportDestinationResolver,
        sample_reservoir_config_vfs_storage: ReservoirConfig,
    ) -> None:
        """Test resolve_storage_namespace returns subpath for VFS storage"""
        result = destination_resolver.resolve_storage_namespace(sample_reservoir_config_vfs_storage)

        assert result == "test-subpath"

    def test_resolve_storage_namespace_vfolder_storage_raises_error(
        self,
        destination_resolver: ArtifactImportDestinationResolver,
        sample_reservoir_config_vfolder_storage: ReservoirConfig,
    ) -> None:
        """Test resolve_storage_namespace raises error for VFolder storage type"""
        with pytest.raises(VFolderStorageNamespaceNotResolvableError):
            destination_resolver.resolve_storage_namespace(sample_reservoir_config_vfolder_storage)

    def test_resolve_storage_namespace_unsupported_type_raises_error(
        self,
        destination_resolver: ArtifactImportDestinationResolver,
    ) -> None:
        """Test resolve_storage_namespace raises error for unsupported storage type"""
        mock_config = MagicMock(spec=ReservoirConfig)
        mock_config.config = MagicMock()
        mock_config.config.storage_type = "unsupported_storage_type"

        with pytest.raises(UnsupportedStorageTypeError):
            destination_resolver.resolve_storage_namespace(mock_config)

    async def test_get_storage_info_object_storage(
        self,
        destination_resolver: ArtifactImportDestinationResolver,
        mock_object_storage_repository: MagicMock,
        mock_storage_namespace_repository: MagicMock,
    ) -> None:
        """Test _get_storage_info returns object storage info when found"""
        storage_id = uuid.uuid4()
        namespace_id = uuid.uuid4()

        mock_storage_data = MagicMock()
        mock_storage_data.id = storage_id
        mock_storage_data.host = "object-storage-host"
        mock_storage_data.name = "object-storage-name"
        mock_object_storage_repository.get_by_name = AsyncMock(return_value=mock_storage_data)

        mock_namespace_data = MagicMock()
        mock_namespace_data.id = namespace_id
        mock_storage_namespace_repository.get_by_storage_and_namespace = AsyncMock(
            return_value=mock_namespace_data
        )

        host, ns_id, name = await destination_resolver._get_storage_info(
            "test-storage", "test-namespace"
        )

        assert host == "object-storage-host"
        assert ns_id == namespace_id
        assert name == "object-storage-name"
        mock_object_storage_repository.get_by_name.assert_called_once_with("test-storage")

    async def test_get_storage_info_fallback_to_vfs_storage(
        self,
        destination_resolver: ArtifactImportDestinationResolver,
        mock_object_storage_repository: MagicMock,
        mock_vfs_storage_repository: MagicMock,
        mock_storage_namespace_repository: MagicMock,
    ) -> None:
        """Test _get_storage_info falls back to VFS storage when object storage fails"""
        storage_id = uuid.uuid4()
        namespace_id = uuid.uuid4()

        # Object storage lookup fails
        mock_object_storage_repository.get_by_name = AsyncMock(side_effect=Exception("Not found"))

        # VFS storage lookup succeeds
        mock_vfs_storage_data = MagicMock()
        mock_vfs_storage_data.id = storage_id
        mock_vfs_storage_data.host = "vfs-storage-host"
        mock_vfs_storage_data.name = "vfs-storage-name"
        mock_vfs_storage_repository.get_by_name = AsyncMock(return_value=mock_vfs_storage_data)

        mock_namespace_data = MagicMock()
        mock_namespace_data.id = namespace_id
        mock_storage_namespace_repository.get_by_storage_and_namespace = AsyncMock(
            return_value=mock_namespace_data
        )

        host, ns_id, name = await destination_resolver._get_storage_info(
            "test-storage", "test-namespace"
        )

        assert host == "vfs-storage-host"
        assert ns_id == namespace_id
        assert name == "vfs-storage-name"
        mock_vfs_storage_repository.get_by_name.assert_called_once_with("test-storage")

    async def test_resolve_storage_destination(
        self,
        destination_resolver: ArtifactImportDestinationResolver,
        mock_object_storage_repository: MagicMock,
        mock_storage_namespace_repository: MagicMock,
        sample_reservoir_config_object_storage: ReservoirConfig,
    ) -> None:
        """Test _resolve_storage_destination returns correct ImportDestinationInfo"""
        storage_id = uuid.uuid4()
        namespace_id = uuid.uuid4()

        mock_storage_data = MagicMock()
        mock_storage_data.id = storage_id
        mock_storage_data.host = "archive-storage-host"
        mock_storage_data.name = "archive-storage"
        mock_object_storage_repository.get_by_name = AsyncMock(return_value=mock_storage_data)

        mock_namespace_data = MagicMock()
        mock_namespace_data.id = namespace_id
        mock_storage_namespace_repository.get_by_storage_and_namespace = AsyncMock(
            return_value=mock_namespace_data
        )

        result = await destination_resolver._resolve_storage_destination(
            sample_reservoir_config_object_storage
        )

        assert isinstance(result, ImportDestinationInfo)
        assert result.storage_host == "archive-storage-host"
        assert result.vfid is None
        assert result.storage_type == ArtifactStorageType.OBJECT_STORAGE.value
        assert result.namespace_id == namespace_id
        assert result.storage_step_mappings == {
            ArtifactStorageImportStep.DOWNLOAD: "download-volume",
            ArtifactStorageImportStep.VERIFY: "verify-volume",
            ArtifactStorageImportStep.ARCHIVE: "archive-volume",
        }
