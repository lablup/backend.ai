"""
Tests for VFSStorageService functionality.
Tests the service layer with mocked repository operations.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.manager.data.vfs_storage.types import VFSStorageData, VFSStorageListResult
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.vfs_storage.repository import VFSStorageRepository
from ai.backend.manager.services.vfs_storage.actions.search import (
    SearchVFSStoragesAction,
)
from ai.backend.manager.services.vfs_storage.service import VFSStorageService


class TestVFSStorageService:
    """Test cases for VFSStorageService"""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        """Create mocked VFSStorageRepository"""
        return MagicMock(spec=VFSStorageRepository)

    @pytest.fixture
    def vfs_storage_service(
        self,
        mock_repository: MagicMock,
    ) -> VFSStorageService:
        """Create VFSStorageService instance with mocked repository"""
        return VFSStorageService(vfs_storage_repository=mock_repository)

    @pytest.fixture
    def sample_vfs_storage_data(self) -> VFSStorageData:
        """Create sample VFS storage data"""
        return VFSStorageData(
            id=uuid4(),
            name="test-vfs-storage",
            host="localhost",
            base_path=Path("/mnt/vfs/test"),
        )

    # =========================================================================
    # Tests - Search
    # =========================================================================

    async def test_search_vfs_storages(
        self,
        vfs_storage_service: VFSStorageService,
        mock_repository: MagicMock,
        sample_vfs_storage_data: VFSStorageData,
    ) -> None:
        """Test searching VFS storages with querier"""
        mock_repository.search = AsyncMock(
            return_value=VFSStorageListResult(
                items=[sample_vfs_storage_data],
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
        action = SearchVFSStoragesAction(querier=querier)
        result = await vfs_storage_service.search(action)

        assert result.storages == [sample_vfs_storage_data]
        assert result.total_count == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False
        mock_repository.search.assert_called_once_with(querier)

    async def test_search_vfs_storages_empty_result(
        self,
        vfs_storage_service: VFSStorageService,
        mock_repository: MagicMock,
    ) -> None:
        """Test searching VFS storages when no results are found"""
        mock_repository.search = AsyncMock(
            return_value=VFSStorageListResult(
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
        action = SearchVFSStoragesAction(querier=querier)
        result = await vfs_storage_service.search(action)

        assert result.storages == []
        assert result.total_count == 0

    async def test_search_vfs_storages_with_pagination(
        self,
        vfs_storage_service: VFSStorageService,
        mock_repository: MagicMock,
        sample_vfs_storage_data: VFSStorageData,
    ) -> None:
        """Test searching VFS storages with pagination"""
        mock_repository.search = AsyncMock(
            return_value=VFSStorageListResult(
                items=[sample_vfs_storage_data],
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
        action = SearchVFSStoragesAction(querier=querier)
        result = await vfs_storage_service.search(action)

        assert result.total_count == 25
        assert result.has_next_page is True
        assert result.has_previous_page is True
