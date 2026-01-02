"""
Unit tests for ContainerRegistryService.
Tests the service layer with mocked repository.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.types import ImageCanonical, ImageID
from ai.backend.manager.container_registry import get_container_registry_cls
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.data.image.types import (
    ImageData,
    ImageLabelsData,
    ImageResourcesData,
    ImageStatus,
    ImageType,
)
from ai.backend.manager.errors.image import ContainerRegistryNotFound
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.container_registry.admin_repository import (
    AdminContainerRegistryRepository,
)
from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)
from ai.backend.manager.services.container_registry.actions.clear_images import ClearImagesAction
from ai.backend.manager.services.container_registry.actions.get_container_registries import (
    GetContainerRegistriesAction,
)
from ai.backend.manager.services.container_registry.actions.load_all_container_registries import (
    LoadAllContainerRegistriesAction,
)
from ai.backend.manager.services.container_registry.actions.load_container_registries import (
    LoadContainerRegistriesAction,
)
from ai.backend.manager.services.container_registry.actions.rescan_images import (
    RescanImagesAction,
)
from ai.backend.manager.services.container_registry.service import ContainerRegistryService

# ==================== Shared Fixtures ====================


@pytest.fixture
def mock_db_engine() -> MagicMock:
    """Create mocked database engine."""
    return MagicMock(spec=ExtendedAsyncSAEngine)


@pytest.fixture
def mock_container_registry_repository() -> MagicMock:
    """Create mocked container registry repository."""
    return MagicMock(spec=ContainerRegistryRepository)


@pytest.fixture
def mock_admin_container_registry_repository() -> MagicMock:
    """Create mocked admin container registry repository."""
    return MagicMock(spec=AdminContainerRegistryRepository)


@pytest.fixture
def container_registry_service(
    mock_db_engine: MagicMock,
    mock_container_registry_repository: MagicMock,
    mock_admin_container_registry_repository: MagicMock,
) -> ContainerRegistryService:
    """Create ContainerRegistryService with mocked dependencies."""
    return ContainerRegistryService(
        db=mock_db_engine,
        container_registry_repository=mock_container_registry_repository,
        admin_container_registry_repository=mock_admin_container_registry_repository,
    )


@pytest.fixture
def sample_registry_data() -> ContainerRegistryData:
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
def sample_registry_data_2() -> ContainerRegistryData:
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


@pytest.fixture
def sample_registries() -> list[ContainerRegistryData]:
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


@pytest.fixture
def sample_registry_row() -> MagicMock:
    """Create sample container registry row."""
    row = MagicMock(spec=ContainerRegistryRow)
    row.id = UUID("12345678-1234-5678-1234-567812345678")
    row.url = "https://registry.example.com"
    row.registry_name = "registry.example.com"
    row.type = ContainerRegistryType.DOCKER
    row.project = "test-project"
    return row


@pytest.fixture
def sample_image_data() -> ImageData:
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
        type=ImageType.COMPUTE,
        status=ImageStatus.ALIVE,
        accelerators="",
        labels=ImageLabelsData(label_data={}),
        resources=ImageResourcesData(resources_data={}),
    )


@pytest.fixture
def sample_known_registries() -> dict[str, str]:
    """Create sample known registries data."""
    return {
        "project1/registry1": "https://registry1.example.com",
        "project2/registry2": "https://registry2.example.com",
        "global-registry": "https://global.example.com",
        "special-project/special-registry": "https://special.registry.com",
    }


# ==================== GetContainerRegistries Tests ====================


class TestGetContainerRegistries:
    """Test cases for ContainerRegistryService.get_container_registries"""

    async def test_success(
        self,
        container_registry_service: ContainerRegistryService,
        mock_container_registry_repository: MagicMock,
        sample_known_registries: dict[str, str],
    ) -> None:
        """Test successfully getting known container registries"""
        mock_container_registry_repository.get_known_registries.return_value = (
            sample_known_registries
        )

        action = GetContainerRegistriesAction()
        result = await container_registry_service.get_container_registries(action)

        assert result.registries == sample_known_registries
        assert len(result.registries) == 4
        assert "project1/registry1" in result.registries
        assert result.registries["project1/registry1"] == "https://registry1.example.com"
        mock_container_registry_repository.get_known_registries.assert_called_once()

    async def test_empty(
        self,
        container_registry_service: ContainerRegistryService,
        mock_container_registry_repository: MagicMock,
    ) -> None:
        """Test getting known registries when none exist"""
        mock_container_registry_repository.get_known_registries.return_value = {}

        action = GetContainerRegistriesAction()
        result = await container_registry_service.get_container_registries(action)

        assert result.registries == {}
        mock_container_registry_repository.get_known_registries.assert_called_once()

    async def test_various_formats(
        self,
        container_registry_service: ContainerRegistryService,
        mock_container_registry_repository: MagicMock,
    ) -> None:
        """Test getting registries with various key formats"""
        known_registries = {
            "simple": "https://simple.com",
            "project/registry": "https://project-registry.com",
            "deep/nested/registry": "https://nested.com",
            "special-chars/reg-123": "https://special.com",
        }
        mock_container_registry_repository.get_known_registries.return_value = known_registries

        action = GetContainerRegistriesAction()
        result = await container_registry_service.get_container_registries(action)

        assert result.registries == known_registries
        assert result.registries["simple"] == "https://simple.com"
        assert result.registries["project/registry"] == "https://project-registry.com"
        assert result.registries["deep/nested/registry"] == "https://nested.com"
        assert result.registries["special-chars/reg-123"] == "https://special.com"

    async def test_error_handling(
        self,
        container_registry_service: ContainerRegistryService,
        mock_container_registry_repository: MagicMock,
    ) -> None:
        """Test error handling when repository raises an exception"""
        mock_container_registry_repository.get_known_registries.side_effect = Exception(
            "Failed to fetch registries"
        )

        action = GetContainerRegistriesAction()
        with pytest.raises(Exception) as exc_info:
            await container_registry_service.get_container_registries(action)

        assert "Failed to fetch registries" in str(exc_info.value)


# ==================== ClearImages Tests ====================


class TestClearImages:
    """Test cases for ContainerRegistryService.clear_images"""

    async def test_success(
        self,
        container_registry_service: ContainerRegistryService,
        mock_admin_container_registry_repository: MagicMock,
        sample_registry_data: ContainerRegistryData,
    ) -> None:
        """Test successful image clearing"""
        mock_admin_container_registry_repository.clear_images_force.return_value = (
            sample_registry_data
        )

        action = ClearImagesAction(registry="registry.example.com", project="test-project")
        result = await container_registry_service.clear_images(action)

        assert result.registry == sample_registry_data
        mock_admin_container_registry_repository.clear_images_force.assert_called_once_with(
            "registry.example.com", "test-project"
        )

    async def test_without_project(
        self,
        container_registry_service: ContainerRegistryService,
        mock_admin_container_registry_repository: MagicMock,
        sample_registry_data: ContainerRegistryData,
    ) -> None:
        """Test clearing images without project filter"""
        mock_admin_container_registry_repository.clear_images_force.return_value = (
            sample_registry_data
        )

        action = ClearImagesAction(registry="registry.example.com", project=None)
        result = await container_registry_service.clear_images(action)

        assert result.registry == sample_registry_data
        mock_admin_container_registry_repository.clear_images_force.assert_called_once_with(
            "registry.example.com", None
        )

    async def test_registry_not_found(
        self,
        container_registry_service: ContainerRegistryService,
        mock_admin_container_registry_repository: MagicMock,
    ) -> None:
        """Test clearing images when registry not found"""
        mock_admin_container_registry_repository.clear_images_force.side_effect = (
            ContainerRegistryNotFound()
        )

        action = ClearImagesAction(registry="non-existent", project="test-project")
        with pytest.raises(ContainerRegistryNotFound):
            await container_registry_service.clear_images(action)

    async def test_delegates_to_admin_repository(
        self,
        container_registry_service: ContainerRegistryService,
        mock_admin_container_registry_repository: MagicMock,
        mock_container_registry_repository: MagicMock,
        sample_registry_data: ContainerRegistryData,
    ) -> None:
        """Test that clear_images uses admin repository, not regular repository"""
        mock_admin_container_registry_repository.clear_images_force.return_value = (
            sample_registry_data
        )

        action = ClearImagesAction(registry="registry.example.com", project="test-project")
        await container_registry_service.clear_images(action)

        mock_admin_container_registry_repository.clear_images_force.assert_called_once()
        mock_container_registry_repository.clear_images.assert_not_called()

    async def test_error_propagation(
        self,
        container_registry_service: ContainerRegistryService,
        mock_admin_container_registry_repository: MagicMock,
    ) -> None:
        """Test that errors are properly propagated"""
        mock_admin_container_registry_repository.clear_images_force.side_effect = Exception(
            "Database error"
        )

        action = ClearImagesAction(registry="registry.example.com", project="test-project")
        with pytest.raises(Exception) as exc_info:
            await container_registry_service.clear_images(action)

        assert "Database error" in str(exc_info.value)


# ==================== LoadContainerRegistries Tests ====================


class TestLoadContainerRegistries:
    """Test cases for ContainerRegistryService.load_container_registries"""

    async def test_with_project_success(
        self,
        container_registry_service: ContainerRegistryService,
        mock_container_registry_repository: MagicMock,
        sample_registry_data: ContainerRegistryData,
    ) -> None:
        """Test loading registries with specific project"""
        mock_container_registry_repository.get_by_registry_and_project.return_value = (
            sample_registry_data
        )

        action = LoadContainerRegistriesAction(
            registry="registry.example.com", project="test-project"
        )
        result = await container_registry_service.load_container_registries(action)

        assert len(result.registries) == 1
        assert result.registries[0] == sample_registry_data
        mock_container_registry_repository.get_by_registry_and_project.assert_called_once_with(
            "registry.example.com", "test-project"
        )

    async def test_with_project_not_found(
        self,
        container_registry_service: ContainerRegistryService,
        mock_container_registry_repository: MagicMock,
    ) -> None:
        """Test loading registries when not found with specific project"""
        mock_container_registry_repository.get_by_registry_and_project.side_effect = (
            ContainerRegistryNotFound()
        )

        action = LoadContainerRegistriesAction(
            registry="registry.example.com", project="non-existent"
        )
        result = await container_registry_service.load_container_registries(action)

        assert result.registries == []

    async def test_without_project(
        self,
        container_registry_service: ContainerRegistryService,
        mock_container_registry_repository: MagicMock,
        sample_registry_data: ContainerRegistryData,
        sample_registry_data_2: ContainerRegistryData,
    ) -> None:
        """Test loading all registries with a specific name"""
        mock_container_registry_repository.get_by_registry_name.return_value = [
            sample_registry_data,
            sample_registry_data_2,
        ]

        action = LoadContainerRegistriesAction(registry="registry.example.com", project=None)
        result = await container_registry_service.load_container_registries(action)

        assert len(result.registries) == 2
        assert result.registries[0] == sample_registry_data
        assert result.registries[1] == sample_registry_data_2
        mock_container_registry_repository.get_by_registry_name.assert_called_once_with(
            "registry.example.com"
        )

    async def test_without_project_empty(
        self,
        container_registry_service: ContainerRegistryService,
        mock_container_registry_repository: MagicMock,
    ) -> None:
        """Test loading registries without project when none exist"""
        mock_container_registry_repository.get_by_registry_name.return_value = []

        action = LoadContainerRegistriesAction(registry="non-existent", project=None)
        result = await container_registry_service.load_container_registries(action)

        assert result.registries == []

    async def test_method_selection(
        self,
        container_registry_service: ContainerRegistryService,
        mock_container_registry_repository: MagicMock,
    ) -> None:
        """Test that correct repository method is called based on project parameter"""
        mock_container_registry_repository.get_by_registry_and_project.side_effect = (
            ContainerRegistryNotFound()
        )
        action_with_project = LoadContainerRegistriesAction(
            registry="registry.example.com", project="test-project"
        )
        await container_registry_service.load_container_registries(action_with_project)

        mock_container_registry_repository.get_by_registry_and_project.assert_called_once()
        mock_container_registry_repository.get_by_registry_name.assert_not_called()

        mock_container_registry_repository.reset_mock()

        mock_container_registry_repository.get_by_registry_name.return_value = []
        action_without_project = LoadContainerRegistriesAction(
            registry="registry.example.com", project=None
        )
        await container_registry_service.load_container_registries(action_without_project)

        mock_container_registry_repository.get_by_registry_name.assert_called_once()
        mock_container_registry_repository.get_by_registry_and_project.assert_not_called()

    async def test_error_handling(
        self,
        container_registry_service: ContainerRegistryService,
        mock_container_registry_repository: MagicMock,
    ) -> None:
        """Test error handling for unexpected errors"""
        mock_container_registry_repository.get_by_registry_name.side_effect = Exception(
            "Database connection error"
        )

        action = LoadContainerRegistriesAction(registry="registry.example.com", project=None)
        with pytest.raises(Exception) as exc_info:
            await container_registry_service.load_container_registries(action)

        assert "Database connection error" in str(exc_info.value)


# ==================== LoadAllContainerRegistries Tests ====================


class TestLoadAllContainerRegistries:
    """Test cases for ContainerRegistryService.load_all_container_registries"""

    async def test_success(
        self,
        container_registry_service: ContainerRegistryService,
        mock_container_registry_repository: MagicMock,
        sample_registries: list[ContainerRegistryData],
    ) -> None:
        """Test successfully loading all container registries"""
        mock_container_registry_repository.get_all.return_value = sample_registries

        action = LoadAllContainerRegistriesAction()
        result = await container_registry_service.load_all_container_registries(action)

        assert len(result.registries) == 3
        assert result.registries == sample_registries
        mock_container_registry_repository.get_all.assert_called_once()

    async def test_empty(
        self,
        container_registry_service: ContainerRegistryService,
        mock_container_registry_repository: MagicMock,
    ) -> None:
        """Test loading all registries when none exist"""
        mock_container_registry_repository.get_all.return_value = []

        action = LoadAllContainerRegistriesAction()
        result = await container_registry_service.load_all_container_registries(action)

        assert result.registries == []
        mock_container_registry_repository.get_all.assert_called_once()

    async def test_various_types(
        self,
        container_registry_service: ContainerRegistryService,
        mock_container_registry_repository: MagicMock,
        sample_registries: list[ContainerRegistryData],
    ) -> None:
        """Test loading registries with various types and configurations"""
        mock_container_registry_repository.get_all.return_value = sample_registries

        action = LoadAllContainerRegistriesAction()
        result = await container_registry_service.load_all_container_registries(action)

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

    async def test_error_handling(
        self,
        container_registry_service: ContainerRegistryService,
        mock_container_registry_repository: MagicMock,
    ) -> None:
        """Test error handling when repository raises an exception"""
        mock_container_registry_repository.get_all.side_effect = Exception(
            "Database connection lost"
        )

        action = LoadAllContainerRegistriesAction()
        with pytest.raises(Exception) as exc_info:
            await container_registry_service.load_all_container_registries(action)

        assert "Database connection lost" in str(exc_info.value)


# ==================== RescanImages Tests ====================


class TestRescanImages:
    """Test cases for ContainerRegistryService.rescan_images"""

    async def test_success(
        self,
        container_registry_service: ContainerRegistryService,
        mock_container_registry_repository: MagicMock,
        sample_registry_row: MagicMock,
        sample_image_data: ImageData,
    ) -> None:
        """Test successful image rescan"""
        mock_container_registry_repository.get_registry_row_for_scanner.return_value = (
            sample_registry_row
        )

        mock_scanner = AsyncMock()
        mock_scanner.rescan_single_registry.return_value = MagicMock(
            images=[sample_image_data], errors=[]
        )

        with patch.object(get_container_registry_cls(sample_registry_row), "__new__") as mock_cls:
            mock_cls.return_value = mock_scanner

            action = RescanImagesAction(
                registry="registry.example.com",
                project="test-project",
                progress_reporter=AsyncMock(),
            )
            result = await container_registry_service.rescan_images(action)

            assert result.registry == sample_registry_row.to_dataclass()
            assert len(result.images) == 1
            assert result.images[0] == sample_image_data
            assert result.errors == []

            mock_container_registry_repository.get_registry_row_for_scanner.assert_called_once_with(
                "registry.example.com", "test-project"
            )
            mock_scanner.rescan_single_registry.assert_called_once_with(action.progress_reporter)

    async def test_registry_not_found(
        self,
        container_registry_service: ContainerRegistryService,
        mock_container_registry_repository: MagicMock,
    ) -> None:
        """Test rescan when registry not found"""
        mock_container_registry_repository.get_registry_row_for_scanner.side_effect = (
            ContainerRegistryNotFound()
        )

        action = RescanImagesAction(
            registry="non-existent", project="test-project", progress_reporter=AsyncMock()
        )
        with pytest.raises(ContainerRegistryNotFound):
            await container_registry_service.rescan_images(action)

    async def test_with_errors(
        self,
        container_registry_service: ContainerRegistryService,
        mock_container_registry_repository: MagicMock,
        sample_registry_row: MagicMock,
        sample_image_data: ImageData,
    ) -> None:
        """Test rescan with some errors from scanner"""
        mock_container_registry_repository.get_registry_row_for_scanner.return_value = (
            sample_registry_row
        )

        mock_scanner = AsyncMock()
        mock_scanner.rescan_single_registry.return_value = MagicMock(
            images=[sample_image_data], errors=["Failed to scan some/image:tag"]
        )

        with patch.object(get_container_registry_cls(sample_registry_row), "__new__") as mock_cls:
            mock_cls.return_value = mock_scanner

            action = RescanImagesAction(
                registry="registry.example.com",
                project="test-project",
                progress_reporter=AsyncMock(),
            )
            result = await container_registry_service.rescan_images(action)

            assert len(result.images) == 1
            assert len(result.errors) == 1
            assert result.errors[0] == "Failed to scan some/image:tag"

    async def test_without_project(
        self,
        container_registry_service: ContainerRegistryService,
        mock_container_registry_repository: MagicMock,
        sample_registry_row: MagicMock,
    ) -> None:
        """Test rescan without project parameter"""
        mock_container_registry_repository.get_registry_row_for_scanner.return_value = (
            sample_registry_row
        )

        mock_scanner = AsyncMock()
        mock_scanner.rescan_single_registry.return_value = MagicMock(images=[], errors=[])

        with patch.object(get_container_registry_cls(sample_registry_row), "__new__") as mock_cls:
            mock_cls.return_value = mock_scanner

            action = RescanImagesAction(
                registry="registry.example.com", project=None, progress_reporter=AsyncMock()
            )
            await container_registry_service.rescan_images(action)

            mock_container_registry_repository.get_registry_row_for_scanner.assert_called_once_with(
                "registry.example.com", None
            )

    async def test_scanner_initialization(
        self,
        container_registry_service: ContainerRegistryService,
        mock_container_registry_repository: MagicMock,
        sample_registry_row: MagicMock,
        mock_db_engine: MagicMock,
    ) -> None:
        """Test that scanner is properly initialized"""
        mock_container_registry_repository.get_registry_row_for_scanner.return_value = (
            sample_registry_row
        )

        mock_scanner_instance = AsyncMock()
        mock_scanner_instance.rescan_single_registry.return_value = MagicMock(images=[], errors=[])
        mock_scanner_cls = MagicMock(return_value=mock_scanner_instance)

        with patch(
            "ai.backend.manager.services.container_registry.service.get_container_registry_cls",
            return_value=mock_scanner_cls,
        ):
            action = RescanImagesAction(
                registry="registry.example.com",
                project="test-project",
                progress_reporter=AsyncMock(),
            )
            await container_registry_service.rescan_images(action)

            mock_scanner_cls.assert_called_once_with(
                mock_db_engine, "registry.example.com", sample_registry_row
            )
