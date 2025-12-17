"""
Tests for ReservoirRegistryService functionality.
Tests the service layer with mocked repository operations.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.manager.data.reservoir_registry.types import (
    ReservoirRegistryData,
    ReservoirRegistryListResult,
)
from ai.backend.manager.repositories.artifact_registry.repository import ArtifactRegistryRepository
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.huggingface_registry.repository import HuggingFaceRepository
from ai.backend.manager.repositories.reservoir_registry.repository import (
    ReservoirRegistryRepository,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.search import (
    SearchReservoirRegistriesAction,
)
from ai.backend.manager.services.artifact_registry.service import ArtifactRegistryService


class TestReservoirRegistryService:
    """Test cases for Reservoir Registry Service"""

    @pytest.fixture
    def mock_reservoir_repository(self) -> MagicMock:
        """Create mocked ReservoirRegistryRepository"""
        return MagicMock(spec=ReservoirRegistryRepository)

    @pytest.fixture
    def artifact_registry_service(
        self,
        mock_reservoir_repository: MagicMock,
    ) -> ArtifactRegistryService:
        """Create ArtifactRegistryService instance with mocked repositories"""
        return ArtifactRegistryService(
            huggingface_registry_repository=MagicMock(spec=HuggingFaceRepository),
            reservoir_repository=mock_reservoir_repository,
            artifact_registry_repository=MagicMock(spec=ArtifactRegistryRepository),
        )

    @pytest.fixture
    def sample_reservoir_data(self) -> ReservoirRegistryData:
        """Create sample reservoir registry data"""
        return ReservoirRegistryData(
            id=uuid4(),
            name="test-reservoir-registry",
            endpoint="https://reservoir.example.com",
            access_key="test-access-key",
            secret_key="test-secret-key",
            api_version="v1",
        )

    async def test_search_reservoir_registries(
        self,
        artifact_registry_service: ArtifactRegistryService,
        mock_reservoir_repository: MagicMock,
        sample_reservoir_data: ReservoirRegistryData,
    ) -> None:
        """Test searching reservoir registries with querier"""
        mock_reservoir_repository.search_registries = AsyncMock(
            return_value=ReservoirRegistryListResult(
                items=[sample_reservoir_data],
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
        action = SearchReservoirRegistriesAction(querier=querier)
        result = await artifact_registry_service.search_reservoir_registries(action)

        assert result.registries == [sample_reservoir_data]
        assert result.total_count == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False
        mock_reservoir_repository.search_registries.assert_called_once_with(querier=querier)

    async def test_search_reservoir_registries_empty_result(
        self,
        artifact_registry_service: ArtifactRegistryService,
        mock_reservoir_repository: MagicMock,
    ) -> None:
        """Test searching reservoir registries when no results are found"""
        mock_reservoir_repository.search_registries = AsyncMock(
            return_value=ReservoirRegistryListResult(
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
        action = SearchReservoirRegistriesAction(querier=querier)
        result = await artifact_registry_service.search_reservoir_registries(action)

        assert result.registries == []
        assert result.total_count == 0

    async def test_search_reservoir_registries_with_pagination(
        self,
        artifact_registry_service: ArtifactRegistryService,
        mock_reservoir_repository: MagicMock,
        sample_reservoir_data: ReservoirRegistryData,
    ) -> None:
        """Test searching reservoir registries with pagination"""
        mock_reservoir_repository.search_registries = AsyncMock(
            return_value=ReservoirRegistryListResult(
                items=[sample_reservoir_data],
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
        action = SearchReservoirRegistriesAction(querier=querier)
        result = await artifact_registry_service.search_reservoir_registries(action)

        assert result.total_count == 25
        assert result.has_next_page is True
        assert result.has_previous_page is True
