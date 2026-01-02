"""
Tests for HuggingFaceRegistryService functionality.
Tests the service layer with mocked repository operations.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.manager.data.huggingface_registry.types import (
    HuggingFaceRegistryData,
    HuggingFaceRegistryListResult,
)
from ai.backend.manager.repositories.artifact_registry.repository import ArtifactRegistryRepository
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.huggingface_registry.repository import HuggingFaceRepository
from ai.backend.manager.repositories.reservoir_registry.repository import (
    ReservoirRegistryRepository,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.search import (
    SearchHuggingFaceRegistriesAction,
)
from ai.backend.manager.services.artifact_registry.service import ArtifactRegistryService


class TestHuggingFaceRegistryService:
    """Test cases for HuggingFace Registry Service"""

    @pytest.fixture
    def mock_huggingface_repository(self) -> MagicMock:
        """Create mocked HuggingFaceRepository"""
        return MagicMock(spec=HuggingFaceRepository)

    @pytest.fixture
    def artifact_registry_service(
        self,
        mock_huggingface_repository: MagicMock,
    ) -> ArtifactRegistryService:
        """Create ArtifactRegistryService instance with mocked repositories"""
        return ArtifactRegistryService(
            huggingface_registry_repository=mock_huggingface_repository,
            reservoir_repository=MagicMock(spec=ReservoirRegistryRepository),
            artifact_registry_repository=MagicMock(spec=ArtifactRegistryRepository),
        )

    @pytest.fixture
    def sample_huggingface_data(self) -> HuggingFaceRegistryData:
        """Create sample HuggingFace registry data"""
        return HuggingFaceRegistryData(
            id=uuid4(),
            name="test-huggingface-registry",
            url="https://huggingface.co",
            token="test-token",
        )

    async def test_search_huggingface_registries(
        self,
        artifact_registry_service: ArtifactRegistryService,
        mock_huggingface_repository: MagicMock,
        sample_huggingface_data: HuggingFaceRegistryData,
    ) -> None:
        """Test searching HuggingFace registries with querier"""
        mock_huggingface_repository.search_registries = AsyncMock(
            return_value=HuggingFaceRegistryListResult(
                items=[sample_huggingface_data],
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
        action = SearchHuggingFaceRegistriesAction(querier=querier)
        result = await artifact_registry_service.search_huggingface_registries(action)

        assert result.registries == [sample_huggingface_data]
        assert result.total_count == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False
        mock_huggingface_repository.search_registries.assert_called_once_with(querier=querier)

    async def test_search_huggingface_registries_empty_result(
        self,
        artifact_registry_service: ArtifactRegistryService,
        mock_huggingface_repository: MagicMock,
    ) -> None:
        """Test searching HuggingFace registries when no results are found"""
        mock_huggingface_repository.search_registries = AsyncMock(
            return_value=HuggingFaceRegistryListResult(
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
        action = SearchHuggingFaceRegistriesAction(querier=querier)
        result = await artifact_registry_service.search_huggingface_registries(action)

        assert result.registries == []
        assert result.total_count == 0

    async def test_search_huggingface_registries_with_pagination(
        self,
        artifact_registry_service: ArtifactRegistryService,
        mock_huggingface_repository: MagicMock,
        sample_huggingface_data: HuggingFaceRegistryData,
    ) -> None:
        """Test searching HuggingFace registries with pagination"""
        mock_huggingface_repository.search_registries = AsyncMock(
            return_value=HuggingFaceRegistryListResult(
                items=[sample_huggingface_data],
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
        action = SearchHuggingFaceRegistriesAction(querier=querier)
        result = await artifact_registry_service.search_huggingface_registries(action)

        assert result.total_count == 25
        assert result.has_next_page is True
        assert result.has_previous_page is True
