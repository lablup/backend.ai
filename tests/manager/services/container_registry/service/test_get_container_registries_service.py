"""
Unit tests for ContainerRegistryService.get_container_registries method.
Tests the service layer with mocked repository.
"""

from unittest.mock import MagicMock

import pytest

from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.container_registry.admin_repository import (
    AdminContainerRegistryRepository,
)
from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)
from ai.backend.manager.services.container_registry.actions.get_container_registries import (
    GetContainerRegistriesAction,
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
def sample_known_registries():
    """Create sample known registries data."""
    return {
        "project1/registry1": "https://registry1.example.com",
        "project2/registry2": "https://registry2.example.com",
        "global-registry": "https://global.example.com",
        "special-project/special-registry": "https://special.registry.com",
    }


class TestGetContainerRegistriesService:
    """Test cases for ContainerRegistryService.get_container_registries"""

    @pytest.mark.asyncio
    async def test_get_container_registries_success(
        self,
        container_registry_service,
        mock_container_registry_repository,
        sample_known_registries,
    ):
        """Test successfully getting known container registries"""
        # Setup mock
        mock_container_registry_repository.get_known_registries.return_value = (
            sample_known_registries
        )

        # Execute
        action = GetContainerRegistriesAction()
        result = await container_registry_service.get_container_registries(action)

        # Verify
        assert result.registries == sample_known_registries
        assert len(result.registries) == 4
        assert "project1/registry1" in result.registries
        assert result.registries["project1/registry1"] == "https://registry1.example.com"
        mock_container_registry_repository.get_known_registries.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_container_registries_empty(
        self, container_registry_service, mock_container_registry_repository
    ):
        """Test getting known registries when none exist"""
        # Setup mock
        mock_container_registry_repository.get_known_registries.return_value = {}

        # Execute
        action = GetContainerRegistriesAction()
        result = await container_registry_service.get_container_registries(action)

        # Verify
        assert result.registries == {}
        mock_container_registry_repository.get_known_registries.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_container_registries_various_formats(
        self, container_registry_service, mock_container_registry_repository
    ):
        """Test getting registries with various key formats"""
        # Setup mock with different registry key formats
        known_registries = {
            "simple": "https://simple.com",  # Global registry
            "project/registry": "https://project-registry.com",  # Project-specific
            "deep/nested/registry": "https://nested.com",  # Deep nesting
            "special-chars/reg-123": "https://special.com",  # Special characters
        }
        mock_container_registry_repository.get_known_registries.return_value = known_registries

        # Execute
        action = GetContainerRegistriesAction()
        result = await container_registry_service.get_container_registries(action)

        # Verify all formats are preserved
        assert result.registries == known_registries
        assert result.registries["simple"] == "https://simple.com"
        assert result.registries["project/registry"] == "https://project-registry.com"
        assert result.registries["deep/nested/registry"] == "https://nested.com"
        assert result.registries["special-chars/reg-123"] == "https://special.com"

    @pytest.mark.asyncio
    async def test_get_container_registries_error_handling(
        self, container_registry_service, mock_container_registry_repository
    ):
        """Test error handling when repository raises an exception"""
        # Setup mock to raise exception
        mock_container_registry_repository.get_known_registries.side_effect = Exception(
            "Failed to fetch registries"
        )

        # Execute and verify
        action = GetContainerRegistriesAction()

        with pytest.raises(Exception) as exc_info:
            await container_registry_service.get_container_registries(action)

        assert "Failed to fetch registries" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_container_registries_ignores_action_parameter(
        self, container_registry_service, mock_container_registry_repository
    ):
        """Test that the action parameter is properly ignored"""
        # Setup mock
        mock_container_registry_repository.get_known_registries.return_value = {}

        # Execute with action (no parameters in GetContainerRegistriesAction)
        action = GetContainerRegistriesAction()
        await container_registry_service.get_container_registries(action)

        # Verify repository method was called without parameters
        mock_container_registry_repository.get_known_registries.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_get_container_registries_returns_dict_not_list(
        self,
        container_registry_service,
        mock_container_registry_repository,
        sample_known_registries,
    ):
        """Test that the result is a dictionary mapping, not a list"""
        # Setup mock
        mock_container_registry_repository.get_known_registries.return_value = (
            sample_known_registries
        )

        # Execute
        action = GetContainerRegistriesAction()
        result = await container_registry_service.get_container_registries(action)

        # Verify result type and structure
        assert isinstance(result.registries, dict)
        assert all(isinstance(k, str) for k in result.registries.keys())
        assert all(isinstance(v, str) for v in result.registries.values())
        # Verify it's a mapping from registry identifier to URL
        for key, value in result.registries.items():
            assert value.startswith("https://") or value.startswith("http://")
