"""
Tests for ArtifactService functionality.
Tests the service layer with mocked repository operations.
Only artifact-related tests. Revision tests are in artifact_revision/test_artifact_revision_service.py
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.manager.data.artifact.types import (
    ArtifactAvailability,
    ArtifactData,
    ArtifactListResult,
    ArtifactType,
)
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.artifact.updaters import ArtifactUpdaterSpec
from ai.backend.manager.repositories.artifact_registry.repository import ArtifactRegistryRepository
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.huggingface_registry.repository import HuggingFaceRepository
from ai.backend.manager.repositories.object_storage.repository import ObjectStorageRepository
from ai.backend.manager.repositories.reservoir_registry.repository import (
    ReservoirRegistryRepository,
)
from ai.backend.manager.repositories.vfs_storage.repository import VFSStorageRepository
from ai.backend.manager.services.artifact.actions.delete_multi import (
    DeleteArtifactsAction,
)
from ai.backend.manager.services.artifact.actions.get import (
    GetArtifactAction,
)
from ai.backend.manager.services.artifact.actions.restore_multi import (
    RestoreArtifactsAction,
)
from ai.backend.manager.services.artifact.actions.search import (
    SearchArtifactsAction,
)
from ai.backend.manager.services.artifact.actions.update import (
    UpdateArtifactAction,
)
from ai.backend.manager.services.artifact.service import ArtifactService
from ai.backend.manager.types import TriState


class TestArtifactService:
    """Test cases for ArtifactService (artifact-only operations)"""

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
        now = datetime.now(timezone.utc)
        registry_id = uuid4()
        return ArtifactData(
            id=uuid4(),
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

    async def test_get_artifact(
        self,
        artifact_service: ArtifactService,
        mock_artifact_repository: MagicMock,
        sample_artifact_data: ArtifactData,
    ) -> None:
        """Test getting an artifact by ID"""
        mock_artifact_repository.get_artifact_by_id = AsyncMock(return_value=sample_artifact_data)

        action = GetArtifactAction(artifact_id=sample_artifact_data.id)
        result = await artifact_service.get(action)

        assert result.result == sample_artifact_data
        mock_artifact_repository.get_artifact_by_id.assert_called_once_with(sample_artifact_data.id)

    async def test_search_artifacts(
        self,
        artifact_service: ArtifactService,
        mock_artifact_repository: MagicMock,
        sample_artifact_data: ArtifactData,
    ) -> None:
        """Test searching artifacts with querier"""
        mock_artifact_repository.search_artifacts = AsyncMock(
            return_value=ArtifactListResult(
                items=[sample_artifact_data],
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
        action = SearchArtifactsAction(querier=querier)
        result = await artifact_service.search(action)

        assert result.data == [sample_artifact_data]
        assert result.total_count == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False
        mock_artifact_repository.search_artifacts.assert_called_once_with(querier=querier)

    async def test_search_artifacts_empty_result(
        self,
        artifact_service: ArtifactService,
        mock_artifact_repository: MagicMock,
    ) -> None:
        """Test searching artifacts when no results are found"""
        mock_artifact_repository.search_artifacts = AsyncMock(
            return_value=ArtifactListResult(
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
        action = SearchArtifactsAction(querier=querier)
        result = await artifact_service.search(action)

        assert result.data == []
        assert result.total_count == 0

    async def test_search_artifacts_with_pagination(
        self,
        artifact_service: ArtifactService,
        mock_artifact_repository: MagicMock,
        sample_artifact_data: ArtifactData,
    ) -> None:
        """Test searching artifacts with pagination"""
        mock_artifact_repository.search_artifacts = AsyncMock(
            return_value=ArtifactListResult(
                items=[sample_artifact_data],
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
        action = SearchArtifactsAction(querier=querier)
        result = await artifact_service.search(action)

        assert result.total_count == 25
        assert result.has_next_page is True
        assert result.has_previous_page is True

    async def test_update_artifact(
        self,
        artifact_service: ArtifactService,
        mock_artifact_repository: MagicMock,
        sample_artifact_data: ArtifactData,
    ) -> None:
        """Test updating an artifact"""
        updater_spec = ArtifactUpdaterSpec(
            description=TriState.update("Updated description"),
        )
        updater = Updater[ArtifactRow](
            spec=updater_spec,
            pk_value=sample_artifact_data.id,
        )
        updated_artifact = ArtifactData(
            id=sample_artifact_data.id,
            name=sample_artifact_data.name,
            type=sample_artifact_data.type,
            description="Updated description",
            registry_id=sample_artifact_data.registry_id,
            source_registry_id=sample_artifact_data.source_registry_id,
            registry_type=sample_artifact_data.registry_type,
            source_registry_type=sample_artifact_data.source_registry_type,
            availability=sample_artifact_data.availability,
            scanned_at=sample_artifact_data.scanned_at,
            updated_at=datetime.now(timezone.utc),
            readonly=sample_artifact_data.readonly,
            extra=sample_artifact_data.extra,
        )
        mock_artifact_repository.update_artifact = AsyncMock(return_value=updated_artifact)

        action = UpdateArtifactAction(updater=updater)
        result = await artifact_service.update(action)

        assert result.result.description == "Updated description"
        mock_artifact_repository.update_artifact.assert_called_once_with(updater)

    async def test_delete_artifacts(
        self,
        artifact_service: ArtifactService,
        mock_artifact_repository: MagicMock,
        sample_artifact_data: ArtifactData,
    ) -> None:
        """Test deleting artifacts"""
        deleted_artifact = ArtifactData(
            id=sample_artifact_data.id,
            name=sample_artifact_data.name,
            type=sample_artifact_data.type,
            description=sample_artifact_data.description,
            registry_id=sample_artifact_data.registry_id,
            source_registry_id=sample_artifact_data.source_registry_id,
            registry_type=sample_artifact_data.registry_type,
            source_registry_type=sample_artifact_data.source_registry_type,
            availability=ArtifactAvailability.DELETED,
            scanned_at=sample_artifact_data.scanned_at,
            updated_at=datetime.now(timezone.utc),
            readonly=sample_artifact_data.readonly,
            extra=sample_artifact_data.extra,
        )
        mock_artifact_repository.delete_artifacts = AsyncMock(return_value=[deleted_artifact])

        action = DeleteArtifactsAction(artifact_ids=[sample_artifact_data.id])
        result = await artifact_service.delete_artifacts(action)

        assert len(result.artifacts) == 1
        assert result.artifacts[0].availability == ArtifactAvailability.DELETED
        mock_artifact_repository.delete_artifacts.assert_called_once_with([sample_artifact_data.id])

    async def test_restore_artifacts(
        self,
        artifact_service: ArtifactService,
        mock_artifact_repository: MagicMock,
        sample_artifact_data: ArtifactData,
    ) -> None:
        """Test restoring deleted artifacts"""
        mock_artifact_repository.restore_artifacts = AsyncMock(return_value=[sample_artifact_data])

        action = RestoreArtifactsAction(artifact_ids=[sample_artifact_data.id])
        result = await artifact_service.restore_artifacts(action)

        assert len(result.artifacts) == 1
        assert result.artifacts[0].availability == ArtifactAvailability.ALIVE
        mock_artifact_repository.restore_artifacts.assert_called_once_with([
            sample_artifact_data.id
        ])
