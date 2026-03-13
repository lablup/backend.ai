"""
Tests for ObjectStorageService functionality.
Tests the service layer with mocked repository operations.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.manager.data.artifact.types import (
    ArtifactAvailability,
    ArtifactData,
    ArtifactRevisionData,
    ArtifactStatus,
    ArtifactType,
)
from ai.backend.manager.data.object_storage.types import (
    ObjectStorageData,
    ObjectStorageListResult,
)
from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData
from ai.backend.manager.errors.artifact import ArtifactNotApproved, ArtifactReadonly
from ai.backend.manager.errors.common import ServerMisconfiguredError
from ai.backend.manager.errors.object_storage import ObjectStorageOperationNotSupported
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.object_storage.repository import ObjectStorageRepository
from ai.backend.manager.repositories.storage_namespace.repository import StorageNamespaceRepository
from ai.backend.manager.services.object_storage.actions.create import (
    CreateObjectStorageAction,
)
from ai.backend.manager.services.object_storage.actions.delete import (
    DeleteObjectStorageAction,
)
from ai.backend.manager.services.object_storage.actions.get import (
    GetObjectStorageAction,
)
from ai.backend.manager.services.object_storage.actions.get_download_presigned_url import (
    GetDownloadPresignedURLAction,
)
from ai.backend.manager.services.object_storage.actions.get_upload_presigned_url import (
    GetUploadPresignedURLAction,
)
from ai.backend.manager.services.object_storage.actions.list import (
    ListObjectStorageAction,
)
from ai.backend.manager.services.object_storage.actions.search import (
    SearchObjectStoragesAction,
)
from ai.backend.manager.services.object_storage.actions.update import (
    UpdateObjectStorageAction,
)
from ai.backend.manager.services.object_storage.service import ObjectStorageService


class TestObjectStorageService:
    """Test cases for ObjectStorageService"""

    @pytest.fixture
    def mock_artifact_repository(self) -> MagicMock:
        return MagicMock(spec=ArtifactRepository)

    @pytest.fixture
    def mock_object_storage_repository(self) -> MagicMock:
        return MagicMock(spec=ObjectStorageRepository)

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
    def object_storage_service(
        self,
        mock_artifact_repository: MagicMock,
        mock_object_storage_repository: MagicMock,
        mock_storage_namespace_repository: MagicMock,
        mock_storage_manager: MagicMock,
        mock_config_provider: MagicMock,
    ) -> ObjectStorageService:
        return ObjectStorageService(
            artifact_repository=mock_artifact_repository,
            object_storage_repository=mock_object_storage_repository,
            storage_namespace_repository=mock_storage_namespace_repository,
            storage_manager=mock_storage_manager,
            config_provider=mock_config_provider,
        )

    @pytest.fixture
    def sample_object_storage_data(self) -> ObjectStorageData:
        return ObjectStorageData(
            id=uuid4(),
            name="test-object-storage",
            host="storage-proxy-1",
            access_key="test-access-key",
            secret_key="test-secret-key",
            endpoint="https://s3.example.com",
            region="us-east-1",
        )

    @pytest.fixture
    def sample_artifact_data(self) -> ArtifactData:
        return ArtifactData(
            id=uuid4(),
            name="test-artifact",
            type=ArtifactType.MODEL,
            description="test artifact",
            registry_id=uuid4(),
            source_registry_id=uuid4(),
            registry_type=ArtifactRegistryType.RESERVOIR,
            source_registry_type=ArtifactRegistryType.RESERVOIR,
            availability=ArtifactAvailability.ALIVE,
            scanned_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            readonly=False,
            extra=None,
        )

    @pytest.fixture
    def sample_revision_data(self, sample_artifact_data: ArtifactData) -> ArtifactRevisionData:
        return ArtifactRevisionData(
            id=uuid4(),
            artifact_id=sample_artifact_data.id,
            version="1.0.0",
            readme=None,
            size=1024,
            status=ArtifactStatus.AVAILABLE,
            remote_status=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            digest=None,
            verification_result=None,
        )

    @pytest.fixture
    def sample_namespace_data(
        self, sample_object_storage_data: ObjectStorageData
    ) -> StorageNamespaceData:
        return StorageNamespaceData(
            id=uuid4(),
            storage_id=sample_object_storage_data.id,
            namespace="test-bucket",
        )

    # =========================================================================
    # Tests - CreateObjectStorageAction
    # =========================================================================

    async def test_create_object_storage(
        self,
        object_storage_service: ObjectStorageService,
        mock_object_storage_repository: MagicMock,
        sample_object_storage_data: ObjectStorageData,
    ) -> None:
        mock_object_storage_repository.create = AsyncMock(return_value=sample_object_storage_data)
        creator = MagicMock()
        action = CreateObjectStorageAction(creator=creator)

        result = await object_storage_service.create(action)

        assert result.result == sample_object_storage_data
        assert result.result.id == sample_object_storage_data.id
        mock_object_storage_repository.create.assert_called_once_with(creator)

    # =========================================================================
    # Tests - GetObjectStorageAction
    # =========================================================================

    async def test_get_object_storage(
        self,
        object_storage_service: ObjectStorageService,
        mock_object_storage_repository: MagicMock,
        sample_object_storage_data: ObjectStorageData,
    ) -> None:
        storage_id = sample_object_storage_data.id
        mock_object_storage_repository.get_by_id = AsyncMock(
            return_value=sample_object_storage_data
        )
        action = GetObjectStorageAction(storage_id=storage_id)

        result = await object_storage_service.get(action)

        assert result.result == sample_object_storage_data
        assert result.result.name == "test-object-storage"
        assert result.result.host == "storage-proxy-1"
        assert result.result.endpoint == "https://s3.example.com"
        mock_object_storage_repository.get_by_id.assert_called_once_with(storage_id)

    async def test_get_object_storage_not_found(
        self,
        object_storage_service: ObjectStorageService,
        mock_object_storage_repository: MagicMock,
    ) -> None:
        non_existent_id = uuid4()
        mock_object_storage_repository.get_by_id = AsyncMock(
            side_effect=Exception("Object storage not found")
        )
        action = GetObjectStorageAction(storage_id=non_existent_id)

        with pytest.raises(Exception, match="Object storage not found"):
            await object_storage_service.get(action)

    # =========================================================================
    # Tests - ListObjectStorageAction
    # =========================================================================

    async def test_list_object_storages(
        self,
        object_storage_service: ObjectStorageService,
        mock_object_storage_repository: MagicMock,
        sample_object_storage_data: ObjectStorageData,
    ) -> None:
        second_storage = ObjectStorageData(
            id=uuid4(),
            name="second-storage",
            host="storage-proxy-2",
            access_key="key2",
            secret_key="secret2",
            endpoint="https://s3-2.example.com",
            region="us-west-2",
        )
        mock_object_storage_repository.list_object_storages = AsyncMock(
            return_value=[sample_object_storage_data, second_storage]
        )
        action = ListObjectStorageAction()

        result = await object_storage_service.list(action)

        assert len(result.data) == 2
        assert result.data[0] == sample_object_storage_data
        assert result.data[1] == second_storage
        mock_object_storage_repository.list_object_storages.assert_called_once()

    async def test_list_object_storages_empty(
        self,
        object_storage_service: ObjectStorageService,
        mock_object_storage_repository: MagicMock,
    ) -> None:
        mock_object_storage_repository.list_object_storages = AsyncMock(return_value=[])
        action = ListObjectStorageAction()

        result = await object_storage_service.list(action)

        assert result.data == []

    # =========================================================================
    # Tests - UpdateObjectStorageAction
    # =========================================================================

    async def test_update_object_storage(
        self,
        object_storage_service: ObjectStorageService,
        mock_object_storage_repository: MagicMock,
    ) -> None:
        updated_data = ObjectStorageData(
            id=uuid4(),
            name="updated-storage",
            host="new-host",
            access_key="new-key",
            secret_key="new-secret",
            endpoint="https://new-endpoint.com",
            region="eu-west-1",
        )
        mock_object_storage_repository.update = AsyncMock(return_value=updated_data)
        updater = MagicMock()
        updater.pk_value = updated_data.id
        action = UpdateObjectStorageAction(updater=updater)

        result = await object_storage_service.update(action)

        assert result.result == updated_data
        assert result.result.name == "updated-storage"
        mock_object_storage_repository.update.assert_called_once_with(updater)

    async def test_update_object_storage_not_found(
        self,
        object_storage_service: ObjectStorageService,
        mock_object_storage_repository: MagicMock,
    ) -> None:
        mock_object_storage_repository.update = AsyncMock(
            side_effect=Exception("Object storage not found")
        )
        updater = MagicMock()
        updater.pk_value = uuid4()
        action = UpdateObjectStorageAction(updater=updater)

        with pytest.raises(Exception, match="Object storage not found"):
            await object_storage_service.update(action)

    # =========================================================================
    # Tests - DeleteObjectStorageAction
    # =========================================================================

    async def test_delete_object_storage(
        self,
        object_storage_service: ObjectStorageService,
        mock_object_storage_repository: MagicMock,
    ) -> None:
        storage_id = uuid4()
        mock_object_storage_repository.delete = AsyncMock(return_value=storage_id)
        action = DeleteObjectStorageAction(storage_id=storage_id)

        result = await object_storage_service.delete(action)

        assert result.deleted_storage_id == storage_id
        mock_object_storage_repository.delete.assert_called_once_with(storage_id)

    async def test_delete_object_storage_not_found(
        self,
        object_storage_service: ObjectStorageService,
        mock_object_storage_repository: MagicMock,
    ) -> None:
        non_existent_id = uuid4()
        mock_object_storage_repository.delete = AsyncMock(
            side_effect=Exception("Object storage not found")
        )
        action = DeleteObjectStorageAction(storage_id=non_existent_id)

        with pytest.raises(Exception, match="Object storage not found"):
            await object_storage_service.delete(action)

    # =========================================================================
    # Tests - GetDownloadPresignedURLAction
    # =========================================================================

    async def test_get_download_presigned_url_available_artifact(
        self,
        object_storage_service: ObjectStorageService,
        mock_object_storage_repository: MagicMock,
        mock_storage_namespace_repository: MagicMock,
        mock_artifact_repository: MagicMock,
        mock_storage_manager: MagicMock,
        mock_config_provider: MagicMock,
        sample_object_storage_data: ObjectStorageData,
        sample_artifact_data: ArtifactData,
        sample_revision_data: ArtifactRevisionData,
        sample_namespace_data: StorageNamespaceData,
    ) -> None:
        reservoir_config = MagicMock()
        reservoir_config.archive_storage = sample_object_storage_data.name
        reservoir_config.config.storage_type = "object_storage"
        reservoir_config.config.bucket_name = "test-bucket"
        mock_config_provider.config.reservoir = reservoir_config

        mock_object_storage_repository.get_by_name = AsyncMock(
            return_value=sample_object_storage_data
        )
        mock_storage_namespace_repository.get_by_storage_and_namespace = AsyncMock(
            return_value=sample_namespace_data
        )
        mock_artifact_repository.get_artifact_revision_by_id = AsyncMock(
            return_value=sample_revision_data
        )
        mock_artifact_repository.get_artifact_by_id = AsyncMock(return_value=sample_artifact_data)

        mock_client = MagicMock()
        presigned_result = MagicMock()
        presigned_result.url = "https://s3.example.com/presigned-download-url"
        mock_client.get_s3_presigned_download_url = AsyncMock(return_value=presigned_result)
        mock_storage_manager.get_manager_facing_client.return_value = mock_client

        action = GetDownloadPresignedURLAction(
            artifact_revision_id=sample_revision_data.id,
            key="model.bin",
        )
        result = await object_storage_service.get_presigned_download_url(action)

        assert result.storage_id == sample_object_storage_data.id
        assert result.presigned_url == "https://s3.example.com/presigned-download-url"

    async def test_get_download_presigned_url_not_available_raises_error(
        self,
        object_storage_service: ObjectStorageService,
        mock_object_storage_repository: MagicMock,
        mock_storage_namespace_repository: MagicMock,
        mock_artifact_repository: MagicMock,
        mock_config_provider: MagicMock,
        sample_object_storage_data: ObjectStorageData,
        sample_artifact_data: ArtifactData,
        sample_namespace_data: StorageNamespaceData,
    ) -> None:
        reservoir_config = MagicMock()
        reservoir_config.archive_storage = sample_object_storage_data.name
        reservoir_config.config.storage_type = "object_storage"
        reservoir_config.config.bucket_name = "test-bucket"
        mock_config_provider.config.reservoir = reservoir_config

        not_available_revision = ArtifactRevisionData(
            id=uuid4(),
            artifact_id=sample_artifact_data.id,
            version="1.0.0",
            readme=None,
            size=1024,
            status=ArtifactStatus.NEEDS_APPROVAL,
            remote_status=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            digest=None,
            verification_result=None,
        )

        mock_object_storage_repository.get_by_name = AsyncMock(
            return_value=sample_object_storage_data
        )
        mock_storage_namespace_repository.get_by_storage_and_namespace = AsyncMock(
            return_value=sample_namespace_data
        )
        mock_artifact_repository.get_artifact_revision_by_id = AsyncMock(
            return_value=not_available_revision
        )
        mock_artifact_repository.get_artifact_by_id = AsyncMock(return_value=sample_artifact_data)

        action = GetDownloadPresignedURLAction(
            artifact_revision_id=not_available_revision.id,
            key="model.bin",
        )

        with pytest.raises(ArtifactNotApproved):
            await object_storage_service.get_presigned_download_url(action)

    async def test_get_download_presigned_url_no_reservoir_config(
        self,
        object_storage_service: ObjectStorageService,
        mock_config_provider: MagicMock,
    ) -> None:
        mock_config_provider.config.reservoir = None

        action = GetDownloadPresignedURLAction(
            artifact_revision_id=uuid4(),
            key="model.bin",
        )

        with pytest.raises(ServerMisconfiguredError):
            await object_storage_service.get_presigned_download_url(action)

    async def test_get_download_presigned_url_non_object_storage_type(
        self,
        object_storage_service: ObjectStorageService,
        mock_config_provider: MagicMock,
    ) -> None:
        reservoir_config = MagicMock()
        reservoir_config.config.storage_type = "vfs_storage"
        mock_config_provider.config.reservoir = reservoir_config

        action = GetDownloadPresignedURLAction(
            artifact_revision_id=uuid4(),
            key="model.bin",
        )

        with pytest.raises(ObjectStorageOperationNotSupported):
            await object_storage_service.get_presigned_download_url(action)

    # =========================================================================
    # Tests - GetUploadPresignedURLAction
    # =========================================================================

    async def test_get_upload_presigned_url(
        self,
        object_storage_service: ObjectStorageService,
        mock_object_storage_repository: MagicMock,
        mock_storage_namespace_repository: MagicMock,
        mock_artifact_repository: MagicMock,
        mock_storage_manager: MagicMock,
        mock_config_provider: MagicMock,
        sample_object_storage_data: ObjectStorageData,
        sample_artifact_data: ArtifactData,
        sample_revision_data: ArtifactRevisionData,
        sample_namespace_data: StorageNamespaceData,
    ) -> None:
        reservoir_config = MagicMock()
        reservoir_config.archive_storage = sample_object_storage_data.name
        reservoir_config.config.storage_type = "object_storage"
        reservoir_config.config.bucket_name = "test-bucket"
        mock_config_provider.config.reservoir = reservoir_config

        mock_object_storage_repository.get_by_name = AsyncMock(
            return_value=sample_object_storage_data
        )
        mock_storage_namespace_repository.get_by_storage_and_namespace = AsyncMock(
            return_value=sample_namespace_data
        )
        mock_artifact_repository.get_artifact_revision_by_id = AsyncMock(
            return_value=sample_revision_data
        )
        mock_artifact_repository.get_artifact_by_id = AsyncMock(return_value=sample_artifact_data)

        mock_client = MagicMock()
        presigned_result = MagicMock()
        presigned_result.url = "https://s3.example.com/presigned-upload-url"
        presigned_result.fields = {"key": "test-artifact/1.0.0/model.bin", "policy": "encoded"}
        mock_client.get_s3_presigned_upload_url = AsyncMock(return_value=presigned_result)
        mock_storage_manager.get_manager_facing_client.return_value = mock_client

        action = GetUploadPresignedURLAction(
            artifact_revision_id=sample_revision_data.id,
            key="model.bin",
        )
        result = await object_storage_service.get_presigned_upload_url(action)

        assert result.storage_id == sample_object_storage_data.id
        assert result.presigned_url == "https://s3.example.com/presigned-upload-url"
        assert result.fields == {"key": "test-artifact/1.0.0/model.bin", "policy": "encoded"}

    async def test_get_upload_presigned_url_no_reservoir_config(
        self,
        object_storage_service: ObjectStorageService,
        mock_config_provider: MagicMock,
    ) -> None:
        mock_config_provider.config.reservoir = None

        action = GetUploadPresignedURLAction(
            artifact_revision_id=uuid4(),
            key="model.bin",
        )

        with pytest.raises(ServerMisconfiguredError):
            await object_storage_service.get_presigned_upload_url(action)

    async def test_get_upload_presigned_url_readonly_artifact(
        self,
        object_storage_service: ObjectStorageService,
        mock_object_storage_repository: MagicMock,
        mock_storage_namespace_repository: MagicMock,
        mock_artifact_repository: MagicMock,
        mock_config_provider: MagicMock,
        sample_object_storage_data: ObjectStorageData,
        sample_revision_data: ArtifactRevisionData,
        sample_namespace_data: StorageNamespaceData,
    ) -> None:
        reservoir_config = MagicMock()
        reservoir_config.archive_storage = sample_object_storage_data.name
        reservoir_config.config.storage_type = "object_storage"
        reservoir_config.config.bucket_name = "test-bucket"
        mock_config_provider.config.reservoir = reservoir_config

        readonly_artifact = ArtifactData(
            id=sample_revision_data.artifact_id,
            name="readonly-artifact",
            type=ArtifactType.MODEL,
            description="readonly",
            registry_id=uuid4(),
            source_registry_id=uuid4(),
            registry_type=ArtifactRegistryType.RESERVOIR,
            source_registry_type=ArtifactRegistryType.RESERVOIR,
            availability=ArtifactAvailability.ALIVE,
            scanned_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            readonly=True,
            extra=None,
        )

        mock_object_storage_repository.get_by_name = AsyncMock(
            return_value=sample_object_storage_data
        )
        mock_storage_namespace_repository.get_by_storage_and_namespace = AsyncMock(
            return_value=sample_namespace_data
        )
        mock_artifact_repository.get_artifact_revision_by_id = AsyncMock(
            return_value=sample_revision_data
        )
        mock_artifact_repository.get_artifact_by_id = AsyncMock(return_value=readonly_artifact)

        action = GetUploadPresignedURLAction(
            artifact_revision_id=sample_revision_data.id,
            key="model.bin",
        )

        with pytest.raises(ArtifactReadonly):
            await object_storage_service.get_presigned_upload_url(action)

    # =========================================================================
    # Tests - Search Object Storages
    # =========================================================================

    async def test_search_object_storages(
        self,
        object_storage_service: ObjectStorageService,
        mock_object_storage_repository: MagicMock,
        sample_object_storage_data: ObjectStorageData,
    ) -> None:
        mock_object_storage_repository.search = AsyncMock(
            return_value=ObjectStorageListResult(
                items=[sample_object_storage_data],
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
        action = SearchObjectStoragesAction(querier=querier)
        result = await object_storage_service.search(action)

        assert result.storages == [sample_object_storage_data]
        assert result.total_count == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False
        mock_object_storage_repository.search.assert_called_once_with(querier=querier)

    async def test_search_object_storages_empty_result(
        self,
        object_storage_service: ObjectStorageService,
        mock_object_storage_repository: MagicMock,
    ) -> None:
        mock_object_storage_repository.search = AsyncMock(
            return_value=ObjectStorageListResult(
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
        action = SearchObjectStoragesAction(querier=querier)
        result = await object_storage_service.search(action)

        assert result.storages == []
        assert result.total_count == 0

    async def test_search_object_storages_with_pagination(
        self,
        object_storage_service: ObjectStorageService,
        mock_object_storage_repository: MagicMock,
        sample_object_storage_data: ObjectStorageData,
    ) -> None:
        mock_object_storage_repository.search = AsyncMock(
            return_value=ObjectStorageListResult(
                items=[sample_object_storage_data],
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
        action = SearchObjectStoragesAction(querier=querier)
        result = await object_storage_service.search(action)

        assert result.total_count == 25
        assert result.has_next_page is True
        assert result.has_previous_page is True
