"""
Tests for StorageNamespaceService functionality.
Tests the service layer with mocked repository operations.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.manager.data.storage_namespace.types import (
    StorageNamespaceData,
    StorageNamespaceListResult,
)
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.storage_namespace.repository import (
    StorageNamespaceRepository,
)
from ai.backend.manager.services.storage_namespace.actions.search import (
    SearchStorageNamespacesAction,
)
from ai.backend.manager.services.storage_namespace.service import StorageNamespaceService


class TestStorageNamespaceService:
    """Test cases for StorageNamespaceService"""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        """Create mocked StorageNamespaceRepository"""
        return MagicMock(spec=StorageNamespaceRepository)

    @pytest.fixture
    def storage_namespace_service(
        self,
        mock_repository: MagicMock,
    ) -> StorageNamespaceService:
        """Create StorageNamespaceService instance with mocked repository"""
        return StorageNamespaceService(storage_namespace_repository=mock_repository)

    @pytest.fixture
    def sample_storage_namespace_data(self) -> StorageNamespaceData:
        """Create sample storage namespace data"""
        return StorageNamespaceData(
            id=uuid4(),
            storage_id=uuid4(),
            namespace="test-namespace",
        )

    # =========================================================================
    # Tests - Search
    # =========================================================================

    async def test_search_storage_namespaces(
        self,
        storage_namespace_service: StorageNamespaceService,
        mock_repository: MagicMock,
        sample_storage_namespace_data: StorageNamespaceData,
    ) -> None:
        """Test searching storage namespaces with querier"""
        mock_repository.search = AsyncMock(
            return_value=StorageNamespaceListResult(
                items=[sample_storage_namespace_data],
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
        action = SearchStorageNamespacesAction(querier=querier)
        result = await storage_namespace_service.search(action)

        assert result.namespaces == [sample_storage_namespace_data]
        assert result.total_count == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False
        mock_repository.search.assert_called_once_with(querier)

    async def test_search_storage_namespaces_empty_result(
        self,
        storage_namespace_service: StorageNamespaceService,
        mock_repository: MagicMock,
    ) -> None:
        """Test searching storage namespaces when no results are found"""
        mock_repository.search = AsyncMock(
            return_value=StorageNamespaceListResult(
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
        action = SearchStorageNamespacesAction(querier=querier)
        result = await storage_namespace_service.search(action)

        assert result.namespaces == []
        assert result.total_count == 0

    async def test_search_storage_namespaces_with_pagination(
        self,
        storage_namespace_service: StorageNamespaceService,
        mock_repository: MagicMock,
        sample_storage_namespace_data: StorageNamespaceData,
    ) -> None:
        """Test searching storage namespaces with pagination"""
        mock_repository.search = AsyncMock(
            return_value=StorageNamespaceListResult(
                items=[sample_storage_namespace_data],
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
        action = SearchStorageNamespacesAction(querier=querier)
        result = await storage_namespace_service.search(action)

        assert result.total_count == 25
        assert result.has_next_page is True
        assert result.has_previous_page is True
