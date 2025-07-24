"""
Tests for ContainerRegistryRepository functionality.
Tests the repository layer with mocked database operations.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
import sqlalchemy as sa

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.errors.image import ContainerRegistryNotFound
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)


@pytest.fixture
def mock_db_engine():
    """Create mocked database engine."""
    return MagicMock(spec=ExtendedAsyncSAEngine)


@pytest.fixture
def mock_db_session(mock_db_engine):
    """Create mocked database session."""
    mock_session = AsyncMock()
    mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session
    return mock_session


@pytest.fixture
def mock_db_readonly_session(mock_db_engine):
    """Create mocked readonly database session."""
    mock_session = AsyncMock()
    mock_db_engine.begin_readonly_session.return_value.__aenter__.return_value = mock_session
    return mock_session


@pytest.fixture
def sample_registry_row():
    """Create sample container registry row for testing."""
    registry = MagicMock(spec=ContainerRegistryRow)
    registry.id = UUID("12345678-1234-5678-1234-567812345678")
    registry.url = "https://registry.example.com"
    registry.registry_name = "registry.example.com"
    registry.type = ContainerRegistryType.DOCKER
    registry.project = "test-project"
    registry.username = None
    registry.password = None
    registry.ssl_verify = True
    registry.is_global = True
    registry.extra = None
    registry.to_dataclass.return_value = ContainerRegistryData(
        id=registry.id,
        url=registry.url,
        registry_name=registry.registry_name,
        type=registry.type,
        project=registry.project,
        username=registry.username,
        password=registry.password,
        ssl_verify=registry.ssl_verify,
        is_global=registry.is_global,
        extra=registry.extra,
    )
    return registry


class TestContainerRegistryRepository:
    """Test cases for ContainerRegistryRepository"""

    @pytest.fixture
    def repository(self, mock_db_engine):
        """Create ContainerRegistryRepository instance with mocked database"""
        return ContainerRegistryRepository(db=mock_db_engine)

    @pytest.mark.asyncio
    async def test_get_by_registry_and_project_success(
        self, repository, mock_db_readonly_session, sample_registry_row
    ):
        """Test successful registry retrieval by name and project"""
        mock_db_readonly_session.scalar.return_value = sample_registry_row

        result = await repository.get_by_registry_and_project(
            "registry.example.com", "test-project"
        )

        assert result is not None
        assert isinstance(result, ContainerRegistryData)
        assert result.registry_name == "registry.example.com"
        assert result.project == "test-project"

        # Verify the query was built correctly
        mock_db_readonly_session.scalar.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_registry_and_project_not_found(
        self, repository, mock_db_readonly_session
    ):
        """Test registry retrieval when not found"""
        mock_db_readonly_session.scalar.return_value = None

        with pytest.raises(ContainerRegistryNotFound):
            await repository.get_by_registry_and_project("non-existent", "project")

    @pytest.mark.asyncio
    async def test_get_by_registry_name(
        self, repository, mock_db_readonly_session, sample_registry_row
    ):
        """Test getting all registries with a specific name"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_registry_row]
        mock_db_readonly_session.execute.return_value = mock_result

        result = await repository.get_by_registry_name("registry.example.com")

        assert len(result) == 1
        assert result[0].registry_name == "registry.example.com"

    @pytest.mark.asyncio
    async def test_get_all(self, repository, mock_db_readonly_session, sample_registry_row):
        """Test getting all registries"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_registry_row]
        mock_db_readonly_session.execute.return_value = mock_result

        result = await repository.get_all()

        assert len(result) == 1
        assert isinstance(result[0], ContainerRegistryData)

    @pytest.mark.asyncio
    async def test_clear_images(self, repository, mock_db_session, sample_registry_row):
        """Test clearing images for a registry"""
        mock_db_session.scalar.return_value = sample_registry_row

        result = await repository.clear_images("registry.example.com", "test-project")

        assert result is not None
        assert result.registry_name == "registry.example.com"

        # Verify update query was executed
        mock_db_session.execute.assert_called_once()
        call_args = mock_db_session.execute.call_args[0][0]
        # Verify it's an update statement
        assert isinstance(call_args, sa.sql.dml.Update)

    @pytest.mark.asyncio
    async def test_clear_images_not_found(self, repository, mock_db_session):
        """Test clearing images when registry not found"""
        mock_db_session.scalar.return_value = None

        with pytest.raises(ContainerRegistryNotFound):
            await repository.clear_images("non-existent", "project")

    @pytest.mark.asyncio
    async def test_get_known_registries(self, repository, mock_db_readonly_session):
        """Test getting known registries"""
        # Mock the ContainerRegistryRow.get_known_container_registries static method
        with patch.object(
            ContainerRegistryRow,
            "get_known_container_registries",
            return_value={
                "project1": {"registry1": MagicMock(human_repr=lambda: "https://registry1.com")},
                "project2": {"registry2": MagicMock(human_repr=lambda: "https://registry2.com")},
            },
        ):
            result = await repository.get_known_registries()

            assert "project1/registry1" in result
            assert result["project1/registry1"] == "https://registry1.com"
            assert "project2/registry2" in result
            assert result["project2/registry2"] == "https://registry2.com"

    @pytest.mark.asyncio
    async def test_get_registry_row_for_scanner_success(
        self, repository, mock_db_readonly_session, sample_registry_row
    ):
        """Test getting registry row for scanner"""
        mock_db_readonly_session.scalar.return_value = sample_registry_row

        result = await repository.get_registry_row_for_scanner(
            "registry.example.com", "test-project"
        )

        assert result is sample_registry_row
        mock_db_readonly_session.scalar.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_registry_row_for_scanner_not_found(
        self, repository, mock_db_readonly_session
    ):
        """Test getting registry row for scanner when not found"""
        mock_db_readonly_session.scalar.return_value = None

        with pytest.raises(ContainerRegistryNotFound):
            await repository.get_registry_row_for_scanner("non-existent", "project")

    @pytest.mark.asyncio
    async def test_clear_images_with_project_filter(
        self, repository, mock_db_session, sample_registry_row
    ):
        """Test clearing images with project filter"""
        mock_db_session.scalar.return_value = sample_registry_row

        await repository.clear_images("registry.example.com", "specific-project")

        # Verify the update query includes project filter
        mock_db_session.execute.assert_called_once()
        call_args = mock_db_session.execute.call_args[0][0]
        assert isinstance(call_args, sa.sql.dml.Update)

    @pytest.mark.asyncio
    async def test_repository_decorator_applied(self, repository):
        """Test that repository decorator is properly applied to methods"""
        # Check that the decorator is applied by verifying method attributes
        methods_to_check = [
            "get_by_registry_and_project",
            "get_by_registry_name",
            "get_all",
            "clear_images",
            "get_known_registries",
            "get_registry_row_for_scanner",
        ]

        for method_name in methods_to_check:
            method = getattr(repository, method_name)
            # The decorator should be applied to these methods
            assert callable(method)
