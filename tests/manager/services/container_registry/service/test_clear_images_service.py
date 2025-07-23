"""
Unit tests for ContainerRegistryService.clear_images method.
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
from ai.backend.manager.services.container_registry.actions.clear_images import ClearImagesAction
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


class TestClearImagesService:
    """Test cases for ContainerRegistryService.clear_images"""

    @pytest.mark.asyncio
    async def test_clear_images_success(
        self,
        container_registry_service,
        mock_admin_container_registry_repository,
        sample_registry_data,
    ):
        """Test successful image clearing"""
        # Setup mock
        mock_admin_container_registry_repository.clear_images_force.return_value = (
            sample_registry_data
        )

        # Execute
        action = ClearImagesAction(registry="registry.example.com", project="test-project")
        result = await container_registry_service.clear_images(action)

        # Verify
        assert result.registry == sample_registry_data
        mock_admin_container_registry_repository.clear_images_force.assert_called_once_with(
            "registry.example.com", "test-project"
        )

    @pytest.mark.asyncio
    async def test_clear_images_without_project(
        self,
        container_registry_service,
        mock_admin_container_registry_repository,
        sample_registry_data,
    ):
        """Test clearing images without project filter"""
        # Setup mock
        mock_admin_container_registry_repository.clear_images_force.return_value = (
            sample_registry_data
        )

        # Execute
        action = ClearImagesAction(registry="registry.example.com", project=None)
        result = await container_registry_service.clear_images(action)

        # Verify
        assert result.registry == sample_registry_data
        mock_admin_container_registry_repository.clear_images_force.assert_called_once_with(
            "registry.example.com", None
        )

    @pytest.mark.asyncio
    async def test_clear_images_registry_not_found(
        self, container_registry_service, mock_admin_container_registry_repository
    ):
        """Test clearing images when registry not found"""
        # Setup mock to raise exception
        mock_admin_container_registry_repository.clear_images_force.side_effect = (
            ContainerRegistryNotFound()
        )

        # Execute and verify
        action = ClearImagesAction(registry="non-existent", project="test-project")

        with pytest.raises(ContainerRegistryNotFound):
            await container_registry_service.clear_images(action)

    @pytest.mark.asyncio
    async def test_clear_images_delegates_to_admin_repository(
        self,
        container_registry_service,
        mock_admin_container_registry_repository,
        mock_container_registry_repository,
        sample_registry_data,
    ):
        """Test that clear_images uses admin repository, not regular repository"""
        # Setup mock
        mock_admin_container_registry_repository.clear_images_force.return_value = (
            sample_registry_data
        )

        # Execute
        action = ClearImagesAction(registry="registry.example.com", project="test-project")
        await container_registry_service.clear_images(action)

        # Verify admin repository was used
        mock_admin_container_registry_repository.clear_images_force.assert_called_once()
        # Verify regular repository was NOT used for clearing
        mock_container_registry_repository.clear_images.assert_not_called()

    @pytest.mark.asyncio
    async def test_clear_images_error_propagation(
        self, container_registry_service, mock_admin_container_registry_repository
    ):
        """Test that errors are properly propagated"""
        # Setup mock to raise a different exception
        mock_admin_container_registry_repository.clear_images_force.side_effect = Exception(
            "Database error"
        )

        # Execute and verify
        action = ClearImagesAction(registry="registry.example.com", project="test-project")

        with pytest.raises(Exception) as exc_info:
            await container_registry_service.clear_images(action)

        assert "Database error" in str(exc_info.value)
