"""
Tests for ObjectStorageService functionality.
Tests the service layer with mocked repository operations.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.manager.data.object_storage.types import (
    ObjectStorageData,
    ObjectStorageListResult,
)
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.object_storage.repository import ObjectStorageRepository
from ai.backend.manager.repositories.storage_namespace.repository import StorageNamespaceRepository
from ai.backend.manager.services.object_storage.actions.search import (
    SearchObjectStoragesAction,
)
from ai.backend.manager.services.object_storage.service import ObjectStorageService


class TestObjectStorageService:
    """Test cases for ObjectStorageService"""

    @pytest.fixture
    def mock_artifact_repository(self) -> MagicMock:
        """Create mocked ArtifactRepository"""
        return MagicMock(spec=ArtifactRepository)

    @pytest.fixture
    def mock_object_storage_repository(self) -> MagicMock:
        """Create mocked ObjectStorageRepository"""
        return MagicMock(spec=ObjectStorageRepository)

    @pytest.fixture
    def mock_storage_namespace_repository(self) -> MagicMock:
        """Create mocked StorageNamespaceRepository"""
        return MagicMock(spec=StorageNamespaceRepository)

    @pytest.fixture
    def mock_storage_manager(self) -> MagicMock:
        """Create mocked StorageSessionManager"""
        return MagicMock()

    @pytest.fixture
    def mock_config_provider(self) -> MagicMock:
        """Create mocked ManagerConfigProvider"""
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
        """Create ObjectStorageService instance with mocked repositories"""
        return ObjectStorageService(
            artifact_repository=mock_artifact_repository,
            object_storage_repository=mock_object_storage_repository,
            storage_namespace_repository=mock_storage_namespace_repository,
            storage_manager=mock_storage_manager,
            config_provider=mock_config_provider,
        )

    @pytest.fixture
    def sample_object_storage_data(self) -> ObjectStorageData:
        """Create sample Object storage data"""
        return ObjectStorageData(
            id=uuid4(),
            name="test-object-storage",
            host="storage-proxy-1",
            access_key="test-access-key",
            secret_key="test-secret-key",
            endpoint="https://s3.example.com",
            region="us-east-1",
        )

    # =========================================================================
    # Tests - Search Object Storages
    # =========================================================================

    async def test_search_object_storages(
        self,
        object_storage_service: ObjectStorageService,
        mock_object_storage_repository: MagicMock,
        sample_object_storage_data: ObjectStorageData,
    ) -> None:
        """Test searching Object storages with querier"""
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
        """Test searching Object storages when no results are found"""
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
        """Test searching Object storages with pagination"""
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
