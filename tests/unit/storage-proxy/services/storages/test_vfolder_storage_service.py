"""Tests for VFolderStorageService functionality."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.data.storage.types import ArtifactStorageImportStep
from ai.backend.common.types import QuotaScopeID, QuotaScopeType, VFolderID
from ai.backend.storage.services.storages.vfolder_storage import (
    VFolderStorageService,
    VFolderStorageSetupResult,
)
from ai.backend.storage.storages.storage_pool import StoragePool
from ai.backend.storage.storages.vfolder_storage import VFolderStorage
from ai.backend.storage.volumes.pool import VolumePool


class TestVFolderStorageServiceSetup:
    """Test cases for VFolderStorageService.setup()."""

    @pytest.fixture
    def mock_volume(self) -> MagicMock:
        """Create mocked Volume."""
        mock = MagicMock()
        mock.mangle_vfpath.return_value = Path("/mnt/vfolder/test-path")
        return mock

    @pytest.fixture
    def mock_volume_pool(self, mock_volume: MagicMock) -> MagicMock:
        """Create mocked VolumePool."""
        mock_pool = MagicMock(spec=VolumePool)

        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_volume)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_pool.get_volume_by_name.return_value = mock_context

        return mock_pool

    @pytest.fixture
    def mock_storage_pool(self) -> MagicMock:
        """Create mocked StoragePool."""
        return MagicMock(spec=StoragePool)

    @pytest.fixture
    def mock_request_id(self) -> Iterator[MagicMock]:
        """Mock current_request_id to return a predictable value."""
        with patch(
            "ai.backend.storage.services.storages.vfolder_storage.current_request_id"
        ) as mock:
            mock.return_value = "test-request-id"
            yield mock

    @pytest.fixture
    def sample_quota_scope_id(self) -> QuotaScopeID:
        """Create sample QuotaScopeID for testing."""
        return QuotaScopeID(QuotaScopeType.USER, uuid.uuid4())

    @pytest.fixture
    def sample_vfid(self, sample_quota_scope_id: QuotaScopeID) -> VFolderID:
        """Create sample VFolderID for testing."""
        return VFolderID(sample_quota_scope_id, uuid.uuid4())

    @pytest.fixture
    def sample_storage_step_mappings(self) -> dict[ArtifactStorageImportStep, str]:
        """Create sample storage step mappings for testing."""
        return {
            ArtifactStorageImportStep.DOWNLOAD: "artifact_volume",
            ArtifactStorageImportStep.ARCHIVE: "artifact_volume",
        }

    async def test_setup_creates_and_registers_vfolder_storage(
        self,
        mock_volume: MagicMock,
        mock_volume_pool: MagicMock,
        mock_storage_pool: MagicMock,
        mock_request_id: MagicMock,
        sample_vfid: VFolderID,
        sample_storage_step_mappings: dict[ArtifactStorageImportStep, str],
    ) -> None:
        """Test that setup creates VFolderStorage and registers it to the pool."""
        service = VFolderStorageService(
            volume_pool=mock_volume_pool,
            storage_pool=mock_storage_pool,
        )

        result = await service.setup(
            vfolder_id=sample_vfid,
            storage_step_mappings=sample_storage_step_mappings,
        )

        expected_storage_name = f"vfolder_storage_{mock_request_id.return_value}"
        expected_volume_name = next(iter(sample_storage_step_mappings.values()))
        expected_base_path = mock_volume.mangle_vfpath.return_value

        # Verify result type and structure
        assert isinstance(result, VFolderStorageSetupResult)

        # Verify volume was retrieved
        mock_volume_pool.get_volume_by_name.assert_called_once_with(expected_volume_name)

        # Verify storage was registered with correct name and instance
        mock_storage_pool.add_storage.assert_called_once()
        registered_name, registered_storage = mock_storage_pool.add_storage.call_args[0]
        assert registered_name == expected_storage_name
        assert isinstance(registered_storage, VFolderStorage)
        assert registered_storage.vfolder_id == sample_vfid
        assert registered_storage.base_path == expected_base_path

        # Verify all mappings point to the new storage
        for step in sample_storage_step_mappings:
            assert result.storage_step_mappings[step] == expected_storage_name

        # Verify cleanup callback removes storage
        result.cleanup_callback()
        mock_storage_pool.remove_storage.assert_called_once_with(expected_storage_name)
