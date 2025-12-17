"""
Tests for ArtifactRegistryService functionality.
Tests the service layer with mocked repository operations.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.manager.data.artifact_registries.types import (
    ArtifactRegistryData,
    ArtifactRegistryListResult,
)
from ai.backend.manager.repositories.artifact_registry.repository import ArtifactRegistryRepository
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.huggingface_registry.repository import HuggingFaceRepository
from ai.backend.manager.repositories.reservoir_registry.repository import (
    ReservoirRegistryRepository,
)
from ai.backend.manager.services.artifact_registry.actions.common.search import (
    SearchArtifactRegistriesAction,
)
from ai.backend.manager.services.artifact_registry.service import ArtifactRegistryService


class TestArtifactRegistryService:
    """Test cases for ArtifactRegistryService"""

    @pytest.fixture
    def mock_huggingface_repository(self) -> MagicMock:
        """Create mocked HuggingFaceRepository"""
        return MagicMock(spec=HuggingFaceRepository)

    @pytest.fixture
    def mock_reservoir_repository(self) -> MagicMock:
        """Create mocked ReservoirRegistryRepository"""
        return MagicMock(spec=ReservoirRegistryRepository)

    @pytest.fixture
    def mock_artifact_registry_repository(self) -> MagicMock:
        """Create mocked ArtifactRegistryRepository"""
        return MagicMock(spec=ArtifactRegistryRepository)

    @pytest.fixture
    def artifact_registry_service(
        self,
        mock_huggingface_repository: MagicMock,
        mock_reservoir_repository: MagicMock,
        mock_artifact_registry_repository: MagicMock,
    ) -> ArtifactRegistryService:
        """Create ArtifactRegistryService instance with mocked repositories"""
        return ArtifactRegistryService(
            huggingface_registry_repository=mock_huggingface_repository,
            reservoir_repository=mock_reservoir_repository,
            artifact_registry_repository=mock_artifact_registry_repository,
        )

    @pytest.fixture
    def sample_registry_data(self) -> ArtifactRegistryData:
        """Create sample artifact registry data"""
        return ArtifactRegistryData(
            id=uuid4(),
            registry_id=uuid4(),
            name="test-huggingface-registry",
            type=ArtifactRegistryType.HUGGINGFACE,
        )

    async def test_search_artifact_registries(
        self,
        artifact_registry_service: ArtifactRegistryService,
        mock_artifact_registry_repository: MagicMock,
        sample_registry_data: ArtifactRegistryData,
    ) -> None:
        """Test searching artifact registries with querier"""
        mock_artifact_registry_repository.search_artifact_registries = AsyncMock(
            return_value=ArtifactRegistryListResult(
                items=[sample_registry_data],
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
        action = SearchArtifactRegistriesAction(querier=querier)
        result = await artifact_registry_service.search_artifact_registries(action)

        assert result.registries == [sample_registry_data]
        assert result.total_count == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False
        mock_artifact_registry_repository.search_artifact_registries.assert_called_once_with(
            querier=querier
        )

    async def test_search_artifact_registries_empty_result(
        self,
        artifact_registry_service: ArtifactRegistryService,
        mock_artifact_registry_repository: MagicMock,
    ) -> None:
        """Test searching artifact registries when no results are found"""
        mock_artifact_registry_repository.search_artifact_registries = AsyncMock(
            return_value=ArtifactRegistryListResult(
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
        action = SearchArtifactRegistriesAction(querier=querier)
        result = await artifact_registry_service.search_artifact_registries(action)

        assert result.registries == []
        assert result.total_count == 0

    async def test_search_artifact_registries_with_pagination(
        self,
        artifact_registry_service: ArtifactRegistryService,
        mock_artifact_registry_repository: MagicMock,
        sample_registry_data: ArtifactRegistryData,
    ) -> None:
        """Test searching artifact registries with pagination"""
        mock_artifact_registry_repository.search_artifact_registries = AsyncMock(
            return_value=ArtifactRegistryListResult(
                items=[sample_registry_data],
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
        action = SearchArtifactRegistriesAction(querier=querier)
        result = await artifact_registry_service.search_artifact_registries(action)

        assert result.total_count == 25
        assert result.has_next_page is True
        assert result.has_previous_page is True
