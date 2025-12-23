"""
Unit tests for ContainerRegistryService.load_container_registries method.
Tests the service layer with mocked repository.
"""

from unittest.mock import MagicMock
from uuid import UUID

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.errors.image import ContainerRegistryNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.container_registry.admin_repository import (
    AdminContainerRegistryRepository,
)
from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)
from ai.backend.manager.services.container_registry.actions.load_container_registries import (
    LoadContainerRegistriesAction,
)
from ai.backend.manager.services.container_registry.service import ContainerRegistryService


@pytest.fixture
def mock_db_engine():
    """Create mocked database engine."""
    return MagicMock(spec=ExtendedAsyncSAEngine)


@pytest.fixture
def mock_container_registry_repository():
    """Create mocked container registry repository."""
    return MagicMock(spec=ContainerRegistryRepository)


@pytest.fixture
def mock_admin_container_registry_repository():
    """Create mocked admin container registry repository."""
    return MagicMock(spec=AdminContainerRegistryRepository)


@pytest.fixture
def container_registry_service(
    mock_db_engine,
    mock_container_registry_repository,
    mock_admin_container_registry_repository,
):
    """Create ContainerRegistryService with mocked dependencies."""
    return ContainerRegistryService(
        db=mock_db_engine,
        container_registry_repository=mock_container_registry_repository,
        admin_container_registry_repository=mock_admin_container_registry_repository,
    )


@pytest.fixture
def sample_registry_data():
    """Create sample container registry data."""
    return ContainerRegistryData(
        id=UUID("12345678-1234-5678-1234-567812345678"),
        url="https://registry.example.com",
        registry_name="registry.example.com",
        type=ContainerRegistryType.DOCKER,
        project="test-project",
        username=None,
        password=None,
        ssl_verify=True,
        is_global=True,
        extra=None,
    )


@pytest.fixture
def sample_registry_data_2():
    """Create another sample container registry data."""
    return ContainerRegistryData(
        id=UUID("87654321-4321-8765-4321-876543218765"),
        url="https://registry.example.com",
        registry_name="registry.example.com",
        type=ContainerRegistryType.DOCKER,
        project="another-project",
        username=None,
        password=None,
        ssl_verify=True,
        is_global=True,
        extra=None,
    )


class TestLoadContainerRegistriesService:
    """Test cases for ContainerRegistryService.load_container_registries"""

    @pytest.mark.asyncio
    async def test_load_container_registries_with_project_success(
        self,
        container_registry_service,
        mock_container_registry_repository,
        sample_registry_data,
    ):
        """Test loading registries with specific project"""
        # Setup mock
        mock_container_registry_repository.get_by_registry_and_project.return_value = (
            sample_registry_data
        )

        # Execute
        action = LoadContainerRegistriesAction(
            registry="registry.example.com", project="test-project"
        )
        result = await container_registry_service.load_container_registries(action)

        # Verify
        assert len(result.registries) == 1
        assert result.registries[0] == sample_registry_data
        mock_container_registry_repository.get_by_registry_and_project.assert_called_once_with(
            "registry.example.com", "test-project"
        )

    @pytest.mark.asyncio
    async def test_load_container_registries_with_project_not_found(
        self, container_registry_service, mock_container_registry_repository
    ):
        """Test loading registries when not found with specific project"""
        # Setup mock to raise exception
        mock_container_registry_repository.get_by_registry_and_project.side_effect = (
            ContainerRegistryNotFound()
        )

        # Execute
        action = LoadContainerRegistriesAction(
            registry="registry.example.com", project="non-existent"
        )
        result = await container_registry_service.load_container_registries(action)

        # Verify empty list is returned
        assert result.registries == []

    @pytest.mark.asyncio
    async def test_load_container_registries_without_project(
        self,
        container_registry_service,
        mock_container_registry_repository,
        sample_registry_data,
        sample_registry_data_2,
    ):
        """Test loading all registries with a specific name"""
        # Setup mock
        mock_container_registry_repository.get_by_registry_name.return_value = [
            sample_registry_data,
            sample_registry_data_2,
        ]

        # Execute
        action = LoadContainerRegistriesAction(registry="registry.example.com", project=None)
        result = await container_registry_service.load_container_registries(action)

        # Verify
        assert len(result.registries) == 2
        assert result.registries[0] == sample_registry_data
        assert result.registries[1] == sample_registry_data_2
        mock_container_registry_repository.get_by_registry_name.assert_called_once_with(
            "registry.example.com"
        )

    @pytest.mark.asyncio
    async def test_load_container_registries_without_project_empty(
        self, container_registry_service, mock_container_registry_repository
    ):
        """Test loading registries without project when none exist"""
        # Setup mock
        mock_container_registry_repository.get_by_registry_name.return_value = []

        # Execute
        action = LoadContainerRegistriesAction(registry="non-existent", project=None)
        result = await container_registry_service.load_container_registries(action)

        # Verify
        assert result.registries == []

    @pytest.mark.asyncio
    async def test_load_container_registries_method_selection(
        self, container_registry_service, mock_container_registry_repository
    ):
        """Test that correct repository method is called based on project parameter"""
        # Test with project - should call get_by_registry_and_project
        action_with_project = LoadContainerRegistriesAction(
            registry="registry.example.com", project="test-project"
        )
        mock_container_registry_repository.get_by_registry_and_project.side_effect = (
            ContainerRegistryNotFound()
        )
        await container_registry_service.load_container_registries(action_with_project)

        mock_container_registry_repository.get_by_registry_and_project.assert_called_once()
        mock_container_registry_repository.get_by_registry_name.assert_not_called()

        # Reset mocks
        mock_container_registry_repository.reset_mock()

        # Test without project - should call get_by_registry_name
        action_without_project = LoadContainerRegistriesAction(
            registry="registry.example.com", project=None
        )
        mock_container_registry_repository.get_by_registry_name.return_value = []
        await container_registry_service.load_container_registries(action_without_project)

        mock_container_registry_repository.get_by_registry_name.assert_called_once()
        mock_container_registry_repository.get_by_registry_and_project.assert_not_called()

    @pytest.mark.asyncio
    async def test_load_container_registries_error_handling(
        self, container_registry_service, mock_container_registry_repository
    ):
        """Test error handling for unexpected errors"""
        # Setup mock to raise unexpected error
        mock_container_registry_repository.get_by_registry_name.side_effect = Exception(
            "Database connection error"
        )

        # Execute and verify
        action = LoadContainerRegistriesAction(registry="registry.example.com", project=None)

        with pytest.raises(Exception) as exc_info:
            await container_registry_service.load_container_registries(action)

        assert "Database connection error" in str(exc_info.value)
