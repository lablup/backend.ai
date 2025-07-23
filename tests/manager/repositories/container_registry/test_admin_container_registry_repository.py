"""
Tests for AdminContainerRegistryRepository functionality.
Tests the admin repository layer with mocked operations.
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


@pytest.fixture
def mock_db_engine():
    """Create mocked database engine."""
    return MagicMock(spec=ExtendedAsyncSAEngine)


@pytest.fixture
def sample_registry_data():
    """Create sample container registry data for testing."""
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


class TestAdminContainerRegistryRepository:
    """Test cases for AdminContainerRegistryRepository"""

    @pytest.fixture
    def admin_repository(self, mock_db_engine):
        """Create AdminContainerRegistryRepository instance with mocked database"""
        return AdminContainerRegistryRepository(db=mock_db_engine)

    @pytest.fixture
    def mock_base_repository(self, admin_repository):
        """Mock the base repository methods"""
        mock_repo = MagicMock(spec=ContainerRegistryRepository)
        admin_repository._repository = mock_repo
        return mock_repo

    @pytest.mark.asyncio
    async def test_clear_images_force_success(
        self, admin_repository, mock_base_repository, sample_registry_data
    ):
        """Test forcefully clearing images"""
        mock_base_repository.clear_images.return_value = sample_registry_data

        result = await admin_repository.clear_images_force("registry.example.com", "test-project")

        assert result == sample_registry_data
        mock_base_repository.clear_images.assert_called_once_with(
            "registry.example.com", "test-project"
        )

    @pytest.mark.asyncio
    async def test_clear_images_force_without_project(
        self, admin_repository, mock_base_repository, sample_registry_data
    ):
        """Test forcefully clearing images without project filter"""
        mock_base_repository.clear_images.return_value = sample_registry_data

        result = await admin_repository.clear_images_force("registry.example.com", None)

        assert result == sample_registry_data
        mock_base_repository.clear_images.assert_called_once_with("registry.example.com", None)

    @pytest.mark.asyncio
    async def test_clear_images_force_error_propagation(
        self, admin_repository, mock_base_repository
    ):
        """Test that errors are properly propagated"""
        mock_base_repository.clear_images.side_effect = ContainerRegistryNotFound()

        with pytest.raises(ContainerRegistryNotFound):
            await admin_repository.clear_images_force("non-existent", "project")

    @pytest.mark.asyncio
    async def test_get_by_registry_and_project_force(
        self, admin_repository, mock_base_repository, sample_registry_data
    ):
        """Test forcefully getting registry by name and project"""
        mock_base_repository.get_by_registry_and_project.return_value = sample_registry_data

        result = await admin_repository.get_by_registry_and_project_force(
            "registry.example.com", "test-project"
        )

        assert result == sample_registry_data
        mock_base_repository.get_by_registry_and_project.assert_called_once_with(
            "registry.example.com", "test-project"
        )

    @pytest.mark.asyncio
    async def test_get_by_registry_name_force(
        self, admin_repository, mock_base_repository, sample_registry_data
    ):
        """Test forcefully getting registries by name"""
        mock_base_repository.get_by_registry_name.return_value = [sample_registry_data]

        result = await admin_repository.get_by_registry_name_force("registry.example.com")

        assert len(result) == 1
        assert result[0] == sample_registry_data
        mock_base_repository.get_by_registry_name.assert_called_once_with("registry.example.com")

    @pytest.mark.asyncio
    async def test_get_all_force(
        self, admin_repository, mock_base_repository, sample_registry_data
    ):
        """Test forcefully getting all registries"""
        mock_base_repository.get_all.return_value = [sample_registry_data]

        result = await admin_repository.get_all_force()

        assert len(result) == 1
        assert result[0] == sample_registry_data
        mock_base_repository.get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_admin_repository_initialization(self, mock_db_engine):
        """Test that admin repository properly initializes with base repository"""
        admin_repo = AdminContainerRegistryRepository(db=mock_db_engine)

        assert admin_repo._repository is not None
        assert isinstance(admin_repo._repository, ContainerRegistryRepository)

    @pytest.mark.asyncio
    async def test_admin_methods_are_force_operations(self, admin_repository, mock_base_repository):
        """Test that all admin methods are force operations without validation"""
        # All admin methods should directly call the base repository methods
        # without additional validation or checks

        methods_to_test = [
            ("clear_images_force", "clear_images", ["registry", "project"]),
            (
                "get_by_registry_and_project_force",
                "get_by_registry_and_project",
                ["registry", "project"],
            ),
            ("get_by_registry_name_force", "get_by_registry_name", ["registry"]),
            ("get_all_force", "get_all", []),
        ]

        for admin_method_name, base_method_name, args in methods_to_test:
            # Reset mock
            base_method = getattr(mock_base_repository, base_method_name)
            base_method.reset_mock()

            # Call admin method
            admin_method = getattr(admin_repository, admin_method_name)
            await admin_method(*args)

            # Verify base method was called
            base_method.assert_called_once()
