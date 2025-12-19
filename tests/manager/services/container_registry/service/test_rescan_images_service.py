"""
Unit tests for ContainerRegistryService.rescan_images method.
Tests the service layer with mocked repository and scanner.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.types import ImageCanonical, ImageID
from ai.backend.manager.container_registry import get_container_registry_cls
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.errors.image import ContainerRegistryNotFound
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.container_registry.admin_repository import (
    AdminContainerRegistryRepository,
)
from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)
from ai.backend.manager.services.container_registry.actions.rescan_images import (
    RescanImagesAction,
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
def sample_registry_row():
    """Create sample container registry row."""
    row = MagicMock(spec=ContainerRegistryRow)
    row.id = UUID("12345678-1234-5678-1234-567812345678")
    row.url = "https://registry.example.com"
    row.registry_name = "registry.example.com"
    row.type = ContainerRegistryType.DOCKER
    row.project = "test-project"
    return row


@pytest.fixture
def sample_image_data():
    """Create sample image data."""
    return ImageData(
        id=ImageID(UUID("87654321-4321-8765-4321-876543218765")),
        name=ImageCanonical("registry.example.com/test-project/python:3.9"),
        project="test-project",
        image="test-project/python",
        created_at=datetime.now(),
        tag="3.9",
        registry="registry.example.com",
        registry_id=UUID("12345678-1234-5678-1234-567812345678"),
        architecture="x86_64",
        config_digest="sha256:" + "a" * 64,
        size_bytes=1000000,
        is_local=False,
        type="compute",
        status="alive",
        accelerators="",
        labels={},
        resources={},
    )


class TestRescanImagesService:
    """Test cases for ContainerRegistryService.rescan_images"""

    @pytest.mark.asyncio
    async def test_rescan_images_success(
        self,
        container_registry_service,
        mock_container_registry_repository,
        sample_registry_row,
        sample_image_data,
    ):
        """Test successful image rescan"""
        # Setup mocks
        mock_container_registry_repository.get_registry_row_for_scanner.return_value = (
            sample_registry_row
        )

        # Mock scanner
        mock_scanner = AsyncMock()
        mock_scanner.rescan_single_registry.return_value = MagicMock(
            images=[sample_image_data], errors=[]
        )

        with patch.object(get_container_registry_cls(sample_registry_row), "__new__") as mock_cls:
            mock_cls.return_value = mock_scanner

            # Execute
            action = RescanImagesAction(
                registry="registry.example.com",
                project="test-project",
                progress_reporter=AsyncMock(),
            )
            result = await container_registry_service.rescan_images(action)

            # Verify
            assert result.registry == sample_registry_row.to_dataclass()
            assert len(result.images) == 1
            assert result.images[0] == sample_image_data
            assert result.errors == []

            # Verify calls
            mock_container_registry_repository.get_registry_row_for_scanner.assert_called_once_with(
                "registry.example.com", "test-project"
            )
            mock_scanner.rescan_single_registry.assert_called_once_with(action.progress_reporter)

    @pytest.mark.asyncio
    async def test_rescan_images_registry_not_found(
        self, container_registry_service, mock_container_registry_repository
    ):
        """Test rescan when registry not found"""
        # Setup mock to raise exception
        mock_container_registry_repository.get_registry_row_for_scanner.side_effect = (
            ContainerRegistryNotFound()
        )

        # Execute and verify
        action = RescanImagesAction(
            registry="non-existent", project="test-project", progress_reporter=AsyncMock()
        )

        with pytest.raises(ContainerRegistryNotFound):
            await container_registry_service.rescan_images(action)

    @pytest.mark.asyncio
    async def test_rescan_images_with_errors(
        self,
        container_registry_service,
        mock_container_registry_repository,
        sample_registry_row,
        sample_image_data,
    ):
        """Test rescan with some errors from scanner"""
        # Setup mocks
        mock_container_registry_repository.get_registry_row_for_scanner.return_value = (
            sample_registry_row
        )

        # Mock scanner with errors
        mock_scanner = AsyncMock()
        mock_scanner.rescan_single_registry.return_value = MagicMock(
            images=[sample_image_data], errors=["Failed to scan some/image:tag"]
        )

        with patch.object(get_container_registry_cls(sample_registry_row), "__new__") as mock_cls:
            mock_cls.return_value = mock_scanner

            # Execute
            action = RescanImagesAction(
                registry="registry.example.com",
                project="test-project",
                progress_reporter=AsyncMock(),
            )
            result = await container_registry_service.rescan_images(action)

            # Verify
            assert len(result.images) == 1
            assert len(result.errors) == 1
            assert result.errors[0] == "Failed to scan some/image:tag"

    @pytest.mark.asyncio
    async def test_rescan_images_without_project(
        self,
        container_registry_service,
        mock_container_registry_repository,
        sample_registry_row,
    ):
        """Test rescan without project parameter"""
        # Setup mocks
        mock_container_registry_repository.get_registry_row_for_scanner.return_value = (
            sample_registry_row
        )

        # Mock scanner
        mock_scanner = AsyncMock()
        mock_scanner.rescan_single_registry.return_value = MagicMock(images=[], errors=[])

        with patch.object(get_container_registry_cls(sample_registry_row), "__new__") as mock_cls:
            mock_cls.return_value = mock_scanner

            # Execute
            action = RescanImagesAction(
                registry="registry.example.com", project=None, progress_reporter=AsyncMock()
            )
            await container_registry_service.rescan_images(action)

            # Verify repository was called with None project
            mock_container_registry_repository.get_registry_row_for_scanner.assert_called_once_with(
                "registry.example.com", None
            )

    @pytest.mark.asyncio
    async def test_rescan_images_scanner_initialization(
        self,
        container_registry_service,
        mock_container_registry_repository,
        sample_registry_row,
        mock_db_engine,
    ):
        """Test that scanner is properly initialized"""
        # Setup mocks
        mock_container_registry_repository.get_registry_row_for_scanner.return_value = (
            sample_registry_row
        )

        # Mock scanner class
        mock_scanner_instance = AsyncMock()
        mock_scanner_instance.rescan_single_registry.return_value = MagicMock(images=[], errors=[])
        mock_scanner_cls = MagicMock(return_value=mock_scanner_instance)

        with patch(
            "ai.backend.manager.services.container_registry.service.get_container_registry_cls",
            return_value=mock_scanner_cls,
        ):
            # Execute
            action = RescanImagesAction(
                registry="registry.example.com",
                project="test-project",
                progress_reporter=AsyncMock(),
            )
            await container_registry_service.rescan_images(action)

            # Verify scanner was initialized with correct parameters
            mock_scanner_cls.assert_called_once_with(
                mock_db_engine, "registry.example.com", sample_registry_row
            )
