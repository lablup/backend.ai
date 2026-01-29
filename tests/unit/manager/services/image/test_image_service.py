"""
Mock-based unit tests for ImageService.

Tests verify service layer business logic using mocked repositories.
"""

from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.dto.agent.response import PurgeImageResp, PurgeImagesResp
from ai.backend.common.exception import UnknownImageReference
from ai.backend.common.types import AgentId, ImageCanonical, ImageID, SlotName
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.data.image.types import (
    ImageAliasData,
    ImageData,
    ImageLabelsData,
    ImageListResult,
    ImageResourcesData,
    RescanImagesResult,
    ResourceLimitInput,
)
from ai.backend.manager.errors.image import (
    ImageAccessForbiddenError,
    ImageAliasNotFound,
    ImageNotFound,
)
from ai.backend.manager.models.image import ImageStatus, ImageType
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.image.repository import ImageRepository
from ai.backend.manager.repositories.image.updaters import ImageUpdaterSpec
from ai.backend.manager.services.image.actions.alias_image import (
    AliasImageAction,
    AliasImageByIdAction,
)
from ai.backend.manager.services.image.actions.clear_image_custom_resource_limit import (
    ClearImageCustomResourceLimitAction,
    ClearImageCustomResourceLimitByIdAction,
)
from ai.backend.manager.services.image.actions.dealias_image import DealiasImageAction
from ai.backend.manager.services.image.actions.forget_image import (
    ForgetImageAction,
    ForgetImageByIdAction,
)
from ai.backend.manager.services.image.actions.modify_image import (
    ModifyImageAction,
    ModifyImageActionUnknownImageReferenceError,
)
from ai.backend.manager.services.image.actions.purge_images import (
    PurgeImageByIdAction,
    PurgeImagesAction,
    PurgeImagesKeyData,
)
from ai.backend.manager.services.image.actions.rescan_images_by_id import RescanImagesByIdAction
from ai.backend.manager.services.image.actions.search_images import SearchImagesAction
from ai.backend.manager.services.image.actions.set_image_resource_limit_by_id import (
    SetImageResourceLimitByIdAction,
)
from ai.backend.manager.services.image.actions.untag_image_from_registry import (
    UntagImageFromRegistryAction,
)
from ai.backend.manager.services.image.processors import ImageProcessors
from ai.backend.manager.services.image.service import ImageService
from ai.backend.manager.services.image.types import ImageRefData
from ai.backend.manager.types import OptionalState, TriState


class ImageServiceBaseFixtures:
    """Base class containing shared fixtures for image service tests."""

    @pytest.fixture
    def mock_image_repository(self) -> MagicMock:
        """Mock ImageRepository for testing."""
        return MagicMock(spec=ImageRepository)

    @pytest.fixture
    def mock_agent_registry(self) -> MagicMock:
        """Mock AgentRegistry for testing."""
        return MagicMock(spec="AgentRegistry")

    @pytest.fixture
    def mock_config_provider(self) -> MagicMock:
        """Mock ManagerConfigProvider for testing."""
        mock = MagicMock()
        mock.config.manager.hide_agents = False
        return mock

    @pytest.fixture
    def image_service(
        self,
        mock_image_repository: MagicMock,
        mock_agent_registry: MagicMock,
        mock_config_provider: MagicMock,
    ) -> ImageService:
        """Create ImageService with mock dependencies."""
        return ImageService(
            agent_registry=mock_agent_registry,
            image_repository=mock_image_repository,
            config_provider=mock_config_provider,
        )

    @pytest.fixture
    def processors(self, image_service: ImageService) -> ImageProcessors:
        """Create ImageProcessors with mock ImageService."""
        return ImageProcessors(image_service, [])

    @pytest.fixture
    def container_registry_id(self) -> uuid.UUID:
        """Container registry ID for test fixtures."""
        return uuid.uuid4()

    @pytest.fixture
    def image_id(self) -> uuid.UUID:
        """Image ID for test fixtures."""
        return uuid.uuid4()

    @pytest.fixture
    def container_registry_data(self, container_registry_id: uuid.UUID) -> ContainerRegistryData:
        """Sample container registry data."""
        return ContainerRegistryData(
            id=container_registry_id,
            url="https://registry.example.com",
            registry_name="registry.example.com",
            type=ContainerRegistryType.DOCKER,
            project="test_project",
            username=None,
            password=None,
            ssl_verify=True,
            is_global=True,
            extra=None,
        )

    @pytest.fixture
    def image_data(self, image_id: uuid.UUID, container_registry_id: uuid.UUID) -> ImageData:
        """Sample image data for testing."""
        return ImageData(
            id=ImageID(image_id),
            name=ImageCanonical("registry.example.com/test_project/python:3.9-ubuntu20.04"),
            image="test_project/python",
            project="test_project",
            tag="3.9-ubuntu20.04",
            registry="registry.example.com",
            registry_id=container_registry_id,
            architecture="x86_64",
            accelerators="cuda",
            config_digest="sha256:abcdefgh0123456789abcdefgh0123456789abcdefgh0123456789abcd".ljust(
                72, " "
            ),
            size_bytes=12345678,
            is_local=False,
            type=ImageType.COMPUTE,
            labels=ImageLabelsData(label_data={}),
            resources=ImageResourcesData(
                resources_data={SlotName("cuda.device"): {"min": "1", "max": None}}
            ),
            status=ImageStatus.ALIVE,
            created_at=datetime(2023, 9, 30, 15, 0, 0, tzinfo=UTC),
        )

    @pytest.fixture
    def image_alias_id(self) -> uuid.UUID:
        """Image alias ID for test fixtures."""
        return uuid.uuid4()

    @pytest.fixture
    def image_alias_data(self, image_alias_id: uuid.UUID) -> ImageAliasData:
        """Sample image alias data for testing."""
        return ImageAliasData(
            id=image_alias_id,
            alias="python",
        )


class TestAliasImage(ImageServiceBaseFixtures):
    """Tests for ImageService.alias_image"""

    async def test_alias_image_success(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
        image_id: uuid.UUID,
        image_alias_data: ImageAliasData,
        image_data: ImageData,
    ) -> None:
        """Alias image with valid data should return image alias."""
        mock_image_repository.add_image_alias = AsyncMock(return_value=(image_id, image_alias_data))

        action = AliasImageAction(
            image_canonical=image_data.name,
            architecture=image_data.architecture,
            alias="python",
        )

        result = await processors.alias_image.wait_for_complete(action)

        assert result.image_id == image_id
        assert result.image_alias == image_alias_data
        mock_image_repository.add_image_alias.assert_called_once_with(
            "python", image_data.name, image_data.architecture
        )

    async def test_alias_image_not_found_raises_error(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
    ) -> None:
        """Alias image with non-existent image should raise ImageNotFound."""
        mock_image_repository.add_image_alias = AsyncMock(
            side_effect=UnknownImageReference("Image not found")
        )

        action = AliasImageAction(
            image_canonical="non-existent-image",
            architecture="x86_64",
            alias="python",
        )

        with pytest.raises(ImageNotFound):
            await processors.alias_image.wait_for_complete(action)


class TestDealiasImage(ImageServiceBaseFixtures):
    """Tests for ImageService.dealias_image"""

    async def test_dealias_image_success(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
        image_id: uuid.UUID,
        image_alias_data: ImageAliasData,
    ) -> None:
        """Dealias image with valid alias should return deleted alias data."""
        mock_image_repository.delete_image_alias = AsyncMock(
            return_value=(image_id, image_alias_data)
        )

        action = DealiasImageAction(alias=image_alias_data.alias)

        result = await processors.dealias_image.wait_for_complete(action)

        assert result.image_id == image_id
        assert result.image_alias == image_alias_data
        mock_image_repository.delete_image_alias.assert_called_once_with(image_alias_data.alias)

    async def test_dealias_image_not_found_raises_error(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
    ) -> None:
        """Dealias non-existent alias should raise ImageAliasNotFound."""
        mock_image_repository.delete_image_alias = AsyncMock(
            side_effect=ImageAliasNotFound("Alias not found")
        )

        action = DealiasImageAction(alias="non-existent-alias")

        with pytest.raises(ImageAliasNotFound):
            await processors.dealias_image.wait_for_complete(action)


class TestForgetImage(ImageServiceBaseFixtures):
    """Tests for ImageService.forget_image"""

    async def test_forget_image_as_superadmin_success(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Superadmin can forget any image."""
        deleted_image = replace(image_data, status=ImageStatus.DELETED)
        mock_image_repository.soft_delete_image = AsyncMock(return_value=deleted_image)

        action = ForgetImageAction(
            user_id=uuid.uuid4(),
            client_role=UserRole.SUPERADMIN,
            reference=image_data.name,
            architecture=image_data.architecture,
        )

        result = await processors.forget_image.wait_for_complete(action)

        assert result.image.status == ImageStatus.DELETED
        mock_image_repository.soft_delete_image.assert_called_once()

    async def test_forget_image_as_user_success(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Regular user can forget image they own."""
        user_id = uuid.uuid4()
        deleted_image = replace(image_data, status=ImageStatus.DELETED)
        mock_image_repository.resolve_image = AsyncMock(return_value=image_data)
        mock_image_repository.validate_image_ownership = AsyncMock(return_value=True)
        mock_image_repository.soft_delete_image = AsyncMock(return_value=deleted_image)

        action = ForgetImageAction(
            user_id=user_id,
            client_role=UserRole.USER,
            reference=image_data.name,
            architecture=image_data.architecture,
        )

        result = await processors.forget_image.wait_for_complete(action)

        assert result.image.status == ImageStatus.DELETED
        mock_image_repository.resolve_image.assert_called_once()
        mock_image_repository.soft_delete_image.assert_called_once()

    async def test_forget_image_as_user_forbidden(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Regular user cannot forget image they don't own."""
        mock_image_repository.resolve_image = AsyncMock(return_value=image_data)
        mock_image_repository.validate_image_ownership = AsyncMock(return_value=False)

        action = ForgetImageAction(
            user_id=uuid.uuid4(),
            client_role=UserRole.USER,
            reference=image_data.name,
            architecture=image_data.architecture,
        )

        with pytest.raises(ImageAccessForbiddenError):
            await processors.forget_image.wait_for_complete(action)

    async def test_forget_image_not_found(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
    ) -> None:
        """Forget non-existent image should raise ImageNotFound."""
        mock_image_repository.soft_delete_image = AsyncMock(side_effect=ImageNotFound())

        action = ForgetImageAction(
            user_id=uuid.uuid4(),
            client_role=UserRole.SUPERADMIN,
            reference="non-existent-image",
            architecture="x86_64",
        )

        with pytest.raises(ImageNotFound):
            await processors.forget_image.wait_for_complete(action)


class TestForgetImageById(ImageServiceBaseFixtures):
    """Tests for ImageService.forget_image_by_id"""

    async def test_forget_image_by_id_as_superadmin_success(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Superadmin can forget any image by ID."""
        deleted_image = replace(image_data, status=ImageStatus.DELETED)
        mock_image_repository.soft_delete_image_by_id = AsyncMock(return_value=deleted_image)

        action = ForgetImageByIdAction(
            user_id=uuid.uuid4(),
            client_role=UserRole.SUPERADMIN,
            image_id=image_data.id,
        )

        result = await processors.forget_image_by_id.wait_for_complete(action)

        assert result.image.status == ImageStatus.DELETED
        mock_image_repository.soft_delete_image_by_id.assert_called_once_with(image_data.id)

    async def test_forget_image_by_id_as_user_success(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Regular user can forget image they own by ID."""
        user_id = uuid.uuid4()
        deleted_image = replace(image_data, status=ImageStatus.DELETED)
        mock_image_repository.validate_image_ownership = AsyncMock(return_value=True)
        mock_image_repository.soft_delete_image_by_id = AsyncMock(return_value=deleted_image)

        action = ForgetImageByIdAction(
            user_id=user_id,
            client_role=UserRole.USER,
            image_id=image_data.id,
        )

        result = await processors.forget_image_by_id.wait_for_complete(action)

        assert result.image.status == ImageStatus.DELETED
        mock_image_repository.validate_image_ownership.assert_called_once()
        mock_image_repository.soft_delete_image_by_id.assert_called_once_with(image_data.id)

    async def test_forget_image_by_id_as_user_forbidden(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Regular user cannot forget image they don't own."""
        mock_image_repository.validate_image_ownership = AsyncMock(return_value=False)

        action = ForgetImageByIdAction(
            user_id=uuid.uuid4(),
            client_role=UserRole.USER,
            image_id=image_data.id,
        )

        with pytest.raises(ImageAccessForbiddenError):
            await processors.forget_image_by_id.wait_for_complete(action)

    async def test_forget_image_by_id_not_found(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
    ) -> None:
        """Forget non-existent image should raise ImageNotFound."""
        mock_image_repository.soft_delete_image_by_id = AsyncMock(side_effect=ImageNotFound())

        action = ForgetImageByIdAction(
            user_id=uuid.uuid4(),
            client_role=UserRole.SUPERADMIN,
            image_id=uuid.uuid4(),
        )

        with pytest.raises(ImageNotFound):
            await processors.forget_image_by_id.wait_for_complete(action)


class TestModifyImage(ImageServiceBaseFixtures):
    """Tests for ImageService.modify_image"""

    async def test_modify_image_update_one_column(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Modify image with single column update should return updated image."""
        updated_image = replace(image_data, registry="cr.backend.ai2")
        mock_image_repository.resolve_image = AsyncMock(return_value=image_data)
        mock_image_repository.update_image_properties = AsyncMock(return_value=updated_image)

        action = ModifyImageAction(
            target=image_data.name,
            architecture=image_data.architecture,
            updater_spec=ImageUpdaterSpec(
                registry=OptionalState.update("cr.backend.ai2"),
            ),
        )

        result = await processors.modify_image.wait_for_complete(action)

        assert result.image.registry == "cr.backend.ai2"
        mock_image_repository.update_image_properties.assert_called_once()

    async def test_modify_image_nullify_column(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Modify image with TriState.nullify should set column to None."""
        updated_image = replace(image_data, accelerators=None)
        mock_image_repository.resolve_image = AsyncMock(return_value=image_data)
        mock_image_repository.update_image_properties = AsyncMock(return_value=updated_image)

        action = ModifyImageAction(
            target=image_data.name,
            architecture=image_data.architecture,
            updater_spec=ImageUpdaterSpec(
                accelerators=TriState.nullify(),
            ),
        )

        result = await processors.modify_image.wait_for_complete(action)

        assert result.image.accelerators is None

    async def test_modify_image_update_multiple_columns(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Modify image with multiple columns should return updated image."""
        new_resources = ImageResourcesData(
            resources_data={
                SlotName("cpu"): {"min": "3", "max": "5"},
                SlotName("mem"): {"min": "256m", "max": None},
            }
        )
        new_labels = ImageLabelsData(label_data={"ai.backend.resource.min.mem": "128m"})
        updated_image = replace(
            image_data,
            type=ImageType.SERVICE,
            registry="cr.backend.ai2",
            accelerators="cuda,rocm",
            is_local=True,
            size_bytes=123,
            labels=new_labels,
            resources=new_resources,
        )
        mock_image_repository.resolve_image = AsyncMock(return_value=image_data)
        mock_image_repository.update_image_properties = AsyncMock(return_value=updated_image)

        action = ModifyImageAction(
            target=image_data.name,
            architecture=image_data.architecture,
            updater_spec=ImageUpdaterSpec(
                image_type=OptionalState.update(ImageType.SERVICE),
                registry=OptionalState.update("cr.backend.ai2"),
                accelerators=TriState.update("cuda,rocm"),
                is_local=OptionalState.update(True),
                size_bytes=OptionalState.update(123),
            ),
        )

        result = await processors.modify_image.wait_for_complete(action)

        assert result.image.type == ImageType.SERVICE
        assert result.image.registry == "cr.backend.ai2"
        assert result.image.is_local is True

    async def test_modify_image_not_found(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
    ) -> None:
        """Modify non-existent image should raise ModifyImageActionUnknownImageReferenceError."""
        mock_image_repository.resolve_image = AsyncMock(
            side_effect=UnknownImageReference("Image not found")
        )

        action = ModifyImageAction(
            target="non-existent-image",
            architecture="x86_64",
            updater_spec=ImageUpdaterSpec(
                registry=OptionalState.update("cr.backend.ai2"),
            ),
        )

        with pytest.raises(ModifyImageActionUnknownImageReferenceError):
            await processors.modify_image.wait_for_complete(action)


class TestPurgeImageById(ImageServiceBaseFixtures):
    """Tests for ImageService.purge_image_by_id"""

    async def test_purge_image_by_id_as_superadmin_success(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Superadmin can purge any image by ID."""
        mock_image_repository.delete_image_with_aliases = AsyncMock(return_value=image_data)

        action = PurgeImageByIdAction(
            user_id=uuid.uuid4(),
            client_role=UserRole.SUPERADMIN,
            image_id=image_data.id,
        )

        result = await processors.purge_image_by_id.wait_for_complete(action)

        assert result.image == image_data
        mock_image_repository.delete_image_with_aliases.assert_called_once_with(image_data.id)

    async def test_purge_image_by_id_as_user_success(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Regular user can purge image they own by ID."""
        user_id = uuid.uuid4()
        mock_image_repository.validate_image_ownership = AsyncMock(return_value=True)
        mock_image_repository.delete_image_with_aliases = AsyncMock(return_value=image_data)

        action = PurgeImageByIdAction(
            user_id=user_id,
            client_role=UserRole.USER,
            image_id=image_data.id,
        )

        result = await processors.purge_image_by_id.wait_for_complete(action)

        assert result.image == image_data
        mock_image_repository.validate_image_ownership.assert_called_once()
        mock_image_repository.delete_image_with_aliases.assert_called_once_with(image_data.id)

    async def test_purge_image_by_id_as_user_forbidden(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Regular user cannot purge image they don't own."""
        mock_image_repository.validate_image_ownership = AsyncMock(return_value=False)

        action = PurgeImageByIdAction(
            user_id=uuid.uuid4(),
            client_role=UserRole.USER,
            image_id=image_data.id,
        )

        with pytest.raises(ImageAccessForbiddenError):
            await processors.purge_image_by_id.wait_for_complete(action)

    async def test_purge_image_by_id_not_found(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
    ) -> None:
        """Purge non-existent image should raise ImageNotFound."""
        mock_image_repository.delete_image_with_aliases = AsyncMock(side_effect=ImageNotFound())

        action = PurgeImageByIdAction(
            user_id=uuid.uuid4(),
            client_role=UserRole.SUPERADMIN,
            image_id=uuid.uuid4(),
        )

        with pytest.raises(ImageNotFound):
            await processors.purge_image_by_id.wait_for_complete(action)


class TestPurgeImages(ImageServiceBaseFixtures):
    """Tests for ImageService.purge_images"""

    async def test_purge_images_success(
        self,
        processors: ImageProcessors,
        mock_agent_registry: MagicMock,
        mock_image_repository: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Purge images should call agent registry and return results."""
        agent_id = AgentId("test-agent")

        # Mock agent registry response
        mock_agent_registry.purge_images = AsyncMock(
            return_value=PurgeImagesResp(
                responses=[
                    PurgeImageResp(image=image_data.name, error=None),
                ]
            )
        )

        # Mock repository batch resolution
        mock_image_repository.resolve_images_batch = AsyncMock(return_value=[image_data])

        action = PurgeImagesAction(
            keys=[
                PurgeImagesKeyData(
                    agent_id=agent_id,
                    images=[
                        ImageRefData(
                            name=image_data.name,
                            registry=image_data.registry,
                            architecture=image_data.architecture,
                        )
                    ],
                )
            ],
            force=False,
            noprune=True,
        )

        result = await processors.purge_images.wait_for_complete(action)

        assert result.total_reserved_bytes == image_data.size_bytes
        assert len(result.purged_images) == 1
        assert result.purged_images[0].agent_id == agent_id
        assert image_data.name in result.purged_images[0].purged_images
        assert len(result.errors) == 0

    async def test_purge_images_with_error(
        self,
        processors: ImageProcessors,
        mock_agent_registry: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Purge images should collect errors from failed agent responses."""
        agent_id = AgentId("test-agent")

        # Mock agent registry response with error
        mock_agent_registry.purge_images = AsyncMock(
            return_value=PurgeImagesResp(
                responses=[
                    PurgeImageResp(image=image_data.name, error="Container in use"),
                ]
            )
        )

        action = PurgeImagesAction(
            keys=[
                PurgeImagesKeyData(
                    agent_id=agent_id,
                    images=[
                        ImageRefData(
                            name=image_data.name,
                            registry=image_data.registry,
                            architecture=image_data.architecture,
                        )
                    ],
                )
            ],
            force=False,
            noprune=True,
        )

        result = await processors.purge_images.wait_for_complete(action)

        assert result.total_reserved_bytes == 0
        assert len(result.errors) == 1
        assert "Container in use" in result.errors[0]


class TestUntagImageFromRegistry(ImageServiceBaseFixtures):
    """Tests for ImageService.untag_image_from_registry"""

    async def test_untag_image_as_superadmin_success(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Superadmin can untag any image from registry."""
        mock_image_repository.untag_image_from_registry = AsyncMock(return_value=image_data)

        action = UntagImageFromRegistryAction(
            user_id=uuid.uuid4(),
            client_role=UserRole.SUPERADMIN,
            image_id=image_data.id,
        )

        result = await processors.untag_image_from_registry.wait_for_complete(action)

        assert result.image == image_data
        mock_image_repository.untag_image_from_registry.assert_called_once_with(image_data.id)

    async def test_untag_image_as_user_success(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Regular user can untag image they own from registry."""
        user_id = uuid.uuid4()
        mock_image_repository.validate_image_ownership = AsyncMock(return_value=True)
        mock_image_repository.untag_image_from_registry = AsyncMock(return_value=image_data)

        action = UntagImageFromRegistryAction(
            user_id=user_id,
            client_role=UserRole.USER,
            image_id=image_data.id,
        )

        result = await processors.untag_image_from_registry.wait_for_complete(action)

        assert result.image == image_data
        mock_image_repository.validate_image_ownership.assert_called_once()
        mock_image_repository.untag_image_from_registry.assert_called_once_with(image_data.id)

    async def test_untag_image_as_user_forbidden(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Regular user cannot untag image they don't own."""
        mock_image_repository.validate_image_ownership = AsyncMock(return_value=False)

        action = UntagImageFromRegistryAction(
            user_id=uuid.uuid4(),
            client_role=UserRole.USER,
            image_id=image_data.id,
        )

        with pytest.raises(ImageAccessForbiddenError):
            await processors.untag_image_from_registry.wait_for_complete(action)

    async def test_untag_image_not_found(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
    ) -> None:
        """Untag non-existent image should raise ImageNotFound."""
        mock_image_repository.untag_image_from_registry = AsyncMock(side_effect=ImageNotFound())

        action = UntagImageFromRegistryAction(
            user_id=uuid.uuid4(),
            client_role=UserRole.SUPERADMIN,
            image_id=uuid.uuid4(),
        )

        with pytest.raises(ImageNotFound):
            await processors.untag_image_from_registry.wait_for_complete(action)


class TestClearImageCustomResourceLimit(ImageServiceBaseFixtures):
    """Tests for ImageService.clear_image_custom_resource_limit"""

    async def test_clear_image_custom_resource_limit_success(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Clear custom resource limit should remove non-intrinsic resources."""
        # Create expected result with cuda.device removed
        cleared_resources = ImageResourcesData(resources_data={})
        expected_image = replace(image_data, resources=cleared_resources)

        mock_image_repository.clear_image_custom_resource_limit = AsyncMock(
            return_value=expected_image
        )

        action = ClearImageCustomResourceLimitAction(
            image_canonical=image_data.name,
            architecture=image_data.architecture,
        )

        result = await processors.clear_image_custom_resource_limit.wait_for_complete(action)

        assert result.image_data.resources.resources_data.get(SlotName("cuda.device")) is None
        mock_image_repository.clear_image_custom_resource_limit.assert_called_once_with(
            image_data.name, image_data.architecture
        )

    async def test_clear_image_custom_resource_limit_not_found(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
    ) -> None:
        """Clear resource limit for non-existent image should raise ImageNotFound."""
        mock_image_repository.clear_image_custom_resource_limit = AsyncMock(
            side_effect=ImageNotFound()
        )

        action = ClearImageCustomResourceLimitAction(
            image_canonical="non-existent-image",
            architecture="x86_64",
        )

        with pytest.raises(ImageNotFound):
            await processors.clear_image_custom_resource_limit.wait_for_complete(action)


class TestSearchImages(ImageServiceBaseFixtures):
    """Tests for ImageService.search_images"""

    async def test_search_images_success(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Search images should return matching results."""
        mock_image_repository.search_images = AsyncMock(
            return_value=ImageListResult(
                items=[image_data],
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
        action = SearchImagesAction(querier=querier)

        result = await processors.search_images.wait_for_complete(action)

        assert result.data == [image_data]
        assert result.total_count == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False
        mock_image_repository.search_images.assert_called_once_with(querier)

    async def test_search_images_empty_result(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
    ) -> None:
        """Search images should return empty list when no results found."""
        mock_image_repository.search_images = AsyncMock(
            return_value=ImageListResult(
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
        action = SearchImagesAction(querier=querier)

        result = await processors.search_images.wait_for_complete(action)

        assert result.data == []
        assert result.total_count == 0

    async def test_search_images_with_pagination(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Search images should handle pagination correctly."""
        mock_image_repository.search_images = AsyncMock(
            return_value=ImageListResult(
                items=[image_data],
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
        action = SearchImagesAction(querier=querier)

        result = await processors.search_images.wait_for_complete(action)

        assert result.total_count == 25
        assert result.has_next_page is True
        assert result.has_previous_page is True


class TestAliasImageById(ImageServiceBaseFixtures):
    """Tests for ImageService.alias_image_by_id"""

    async def test_alias_image_by_id_success(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
        image_id: uuid.UUID,
        image_alias_data: ImageAliasData,
    ) -> None:
        """Alias image by ID with valid data should return image alias."""
        mock_image_repository.add_image_alias_by_id = AsyncMock(
            return_value=(image_id, image_alias_data)
        )

        action = AliasImageByIdAction(
            image_id=image_id,
            alias="python",
        )

        result = await processors.alias_image_by_id.wait_for_complete(action)

        assert result.image_id == image_id
        assert result.image_alias == image_alias_data
        mock_image_repository.add_image_alias_by_id.assert_called_once_with(image_id, "python")


class TestClearImageCustomResourceLimitById(ImageServiceBaseFixtures):
    """Tests for ImageService.clear_image_custom_resource_limit_by_id"""

    async def test_clear_image_custom_resource_limit_by_id_success(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Clear custom resource limit by ID should remove resources."""
        cleared_resources = ImageResourcesData(resources_data={})
        expected_image = replace(image_data, resources=cleared_resources)
        mock_image_repository.clear_image_resource_limits_by_id = AsyncMock(
            return_value=expected_image
        )

        action = ClearImageCustomResourceLimitByIdAction(image_id=image_data.id)

        result = await processors.clear_image_custom_resource_limit_by_id.wait_for_complete(action)

        assert result.image_data.resources.resources_data.get(SlotName("cuda.device")) is None
        mock_image_repository.clear_image_resource_limits_by_id.assert_called_once_with(
            image_data.id
        )

    async def test_clear_image_custom_resource_limit_by_id_not_found(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
    ) -> None:
        """Clear resource limit for non-existent image should raise ImageNotFound."""
        mock_image_repository.clear_image_resource_limits_by_id = AsyncMock(
            side_effect=ImageNotFound()
        )

        action = ClearImageCustomResourceLimitByIdAction(image_id=uuid.uuid4())

        with pytest.raises(ImageNotFound):
            await processors.clear_image_custom_resource_limit_by_id.wait_for_complete(action)


class TestRescanImagesById(ImageServiceBaseFixtures):
    """Tests for ImageService.rescan_images_by_id"""

    async def test_rescan_images_by_id_success(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Rescan images by ID should return scanned images."""
        mock_image_repository.scan_images_by_ids = AsyncMock(
            return_value=RescanImagesResult(images=[image_data], errors=[])
        )

        action = RescanImagesByIdAction(image_ids=[image_data.id])

        result = await processors.rescan_images_by_id.wait_for_complete(action)

        assert len(result.images) == 1
        assert result.images[0] == image_data
        assert len(result.errors) == 0
        mock_image_repository.scan_images_by_ids.assert_called_once_with([image_data.id])

    async def test_rescan_images_by_id_with_errors(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Rescan images by ID should collect errors."""
        mock_image_repository.scan_images_by_ids = AsyncMock(
            return_value=RescanImagesResult(
                images=[image_data], errors=["Registry not found for image test"]
            )
        )

        action = RescanImagesByIdAction(image_ids=[image_data.id, uuid.uuid4()])

        result = await processors.rescan_images_by_id.wait_for_complete(action)

        assert len(result.images) == 1
        assert len(result.errors) == 1
        assert "Registry not found" in result.errors[0]


class TestSetImageResourceLimitById(ImageServiceBaseFixtures):
    """Tests for ImageService.set_image_resource_limit_by_id"""

    async def test_set_image_resource_limit_by_id_success(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Set image resource limit by ID should update resources."""
        new_resources = ImageResourcesData(
            resources_data={SlotName("cpu"): {"min": "2", "max": "4"}}
        )
        expected_image = replace(image_data, resources=new_resources)
        mock_image_repository.set_image_resource_limit_by_id = AsyncMock(
            return_value=expected_image
        )

        resource_limit = ResourceLimitInput(
            slot_name="cpu",
            min_value=Decimal("2"),
            max_value=Decimal("4"),
        )
        action = SetImageResourceLimitByIdAction(
            image_id=image_data.id,
            resource_limit=resource_limit,
        )

        result = await processors.set_image_resource_limit_by_id.wait_for_complete(action)

        assert result.image_data.resources.resources_data.get(SlotName("cpu")) is not None
        mock_image_repository.set_image_resource_limit_by_id.assert_called_once_with(
            image_data.id, resource_limit
        )

    async def test_set_image_resource_limit_by_id_not_found(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
    ) -> None:
        """Set resource limit for non-existent image should raise ImageNotFound."""
        mock_image_repository.set_image_resource_limit_by_id = AsyncMock(
            side_effect=ImageNotFound()
        )

        action = SetImageResourceLimitByIdAction(
            image_id=uuid.uuid4(),
            resource_limit=ResourceLimitInput(
                slot_name="cpu",
                min_value=Decimal("1"),
                max_value=Decimal("2"),
            ),
        )

        with pytest.raises(ImageNotFound):
            await processors.set_image_resource_limit_by_id.wait_for_complete(action)
