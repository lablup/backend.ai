"""
Unit tests for ContainerRegistryService.load_all_container_registries method.
Tests the service layer with mocked repository.
"""

from unittest.mock import MagicMock
from uuid import UUID

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.container_registry.admin_repository import (
    AdminContainerRegistryRepository,
)
from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)
from ai.backend.manager.services.container_registry.actions.load_all_container_registries import (
    LoadAllContainerRegistriesAction,
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
def sample_registries():
    """Create sample container registry data list."""
    return [
        ContainerRegistryData(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            url="https://registry1.example.com",
            registry_name="registry1.example.com",
            type=ContainerRegistryType.DOCKER,
            project="project1",
            username=None,
            password=None,
            ssl_verify=True,
            is_global=True,
            extra=None,
        ),
        ContainerRegistryData(
            id=UUID("87654321-4321-8765-4321-876543218765"),
            url="https://registry2.example.com",
            registry_name="registry2.example.com",
            type=ContainerRegistryType.DOCKER,
            project="project2",
            username="user",
            password="pass",
            ssl_verify=False,
            is_global=False,
            extra={"custom": "data"},
        ),
        ContainerRegistryData(
            id=UUID("11111111-2222-3333-4444-555555555555"),
            url="https://global-registry.example.com",
            registry_name="global-registry.example.com",
            type=ContainerRegistryType.HARBOR2,
            project=None,
            username=None,
            password=None,
            ssl_verify=True,
            is_global=True,
            extra=None,
        ),
    ]


class TestLoadAllContainerRegistriesService:
    """Test cases for ContainerRegistryService.load_all_container_registries"""

    @pytest.mark.asyncio
    async def test_load_all_container_registries_success(
        self,
        container_registry_service,
        mock_container_registry_repository,
        sample_registries,
    ):
        """Test successfully loading all container registries"""
        # Setup mock
        mock_container_registry_repository.get_all.return_value = sample_registries

        # Execute
        action = LoadAllContainerRegistriesAction()
        result = await container_registry_service.load_all_container_registries(action)

        # Verify
        assert len(result.registries) == 3
        assert result.registries == sample_registries
        mock_container_registry_repository.get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_all_container_registries_empty(
        self, container_registry_service, mock_container_registry_repository
    ):
        """Test loading all registries when none exist"""
        # Setup mock
        mock_container_registry_repository.get_all.return_value = []

        # Execute
        action = LoadAllContainerRegistriesAction()
        result = await container_registry_service.load_all_container_registries(action)

        # Verify
        assert result.registries == []
        mock_container_registry_repository.get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_all_container_registries_various_types(
        self,
        container_registry_service,
        mock_container_registry_repository,
        sample_registries,
    ):
        """Test loading registries with various types and configurations"""
        # Setup mock
        mock_container_registry_repository.get_all.return_value = sample_registries

        # Execute
        action = LoadAllContainerRegistriesAction()
        result = await container_registry_service.load_all_container_registries(action)

        # Verify different registry types and configurations
        registries = result.registries

        # Check first registry (basic Docker registry)
        assert registries[0].type == ContainerRegistryType.DOCKER
        assert registries[0].is_global is True
        assert registries[0].username is None

        # Check second registry (authenticated registry)
        assert registries[1].username == "user"
        assert registries[1].password == "pass"
        assert registries[1].ssl_verify is False
        assert registries[1].is_global is False
        assert registries[1].extra == {"custom": "data"}

        # Check third registry (Harbor2 global registry)
        assert registries[2].type == ContainerRegistryType.HARBOR2
        assert registries[2].project is None
        assert registries[2].is_global is True

    @pytest.mark.asyncio
    async def test_load_all_container_registries_error_handling(
        self, container_registry_service, mock_container_registry_repository
    ):
        """Test error handling when repository raises an exception"""
        # Setup mock to raise exception
        mock_container_registry_repository.get_all.side_effect = Exception(
            "Database connection lost"
        )

        # Execute and verify
        action = LoadAllContainerRegistriesAction()

        with pytest.raises(Exception) as exc_info:
            await container_registry_service.load_all_container_registries(action)

        assert "Database connection lost" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_load_all_container_registries_ignores_action_parameter(
        self, container_registry_service, mock_container_registry_repository
    ):
        """Test that the action parameter is properly ignored"""
        # Setup mock
        mock_container_registry_repository.get_all.return_value = []

        # Execute with action (no parameters in LoadAllContainerRegistriesAction)
        action = LoadAllContainerRegistriesAction()
        await container_registry_service.load_all_container_registries(action)

        # Verify repository method was called without parameters
        mock_container_registry_repository.get_all.assert_called_once_with()
