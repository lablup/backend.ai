"""
Mock-based unit tests for ImageService.

Tests verify service layer business logic using mocked repositories.
"""

from __future__ import annotations

import uuid
from dataclasses import replace
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.dto.agent.response import PurgeImageResp, PurgeImagesResp
from ai.backend.common.exception import UnknownImageReference
from ai.backend.common.types import AgentId, SlotName
from ai.backend.manager.data.image.types import (
    ImageAliasData,
    ImageData,
    ImageLabelsData,
    ImageResourcesData,
)
from ai.backend.manager.errors.image import (
    ForgetImageForbiddenError,
    ImageAliasNotFound,
    ImageNotFound,
)
from ai.backend.manager.models.image import ImageStatus, ImageType
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.repositories.image.updaters import ImageUpdaterSpec
from ai.backend.manager.services.image.actions.alias_image import AliasImageAction
from ai.backend.manager.services.image.actions.clear_image_custom_resource_limit import (
    ClearImageCustomResourceLimitAction,
)
from ai.backend.manager.services.image.actions.dealias_image import DealiasImageAction
from ai.backend.manager.services.image.actions.forget_image import ForgetImageAction
from ai.backend.manager.services.image.actions.forget_image_by_id import ForgetImageByIdAction
from ai.backend.manager.services.image.actions.modify_image import (
    ModifyImageAction,
    ModifyImageActionUnknownImageReferenceError,
)
from ai.backend.manager.services.image.actions.purge_image_by_id import PurgeImageByIdAction
from ai.backend.manager.services.image.actions.purge_images import (
    PurgeImagesAction,
    PurgeImagesKeyData,
)
from ai.backend.manager.services.image.actions.untag_image_from_registry import (
    UntagImageFromRegistryAction,
)
from ai.backend.manager.services.image.processors import ImageProcessors
from ai.backend.manager.services.image.types import ImageRefData
from ai.backend.manager.types import OptionalState, TriState


class TestAliasImage:
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


class TestDealiasImage:
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


class TestForgetImage:
    """Tests for ImageService.forget_image"""

    async def test_forget_image_as_superadmin_success(
        self,
        processors: ImageProcessors,
        mock_admin_image_repository: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Superadmin can forget any image."""
        deleted_image = replace(image_data, status=ImageStatus.DELETED)
        mock_admin_image_repository.soft_delete_image_force = AsyncMock(return_value=deleted_image)

        action = ForgetImageAction(
            user_id=uuid.uuid4(),
            client_role=UserRole.SUPERADMIN,
            reference=image_data.name,
            architecture=image_data.architecture,
        )

        result = await processors.forget_image.wait_for_complete(action)

        assert result.image.status == ImageStatus.DELETED
        mock_admin_image_repository.soft_delete_image_force.assert_called_once()

    async def test_forget_image_as_user_forbidden(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Regular user cannot forget image they don't own."""
        mock_image_repository.soft_delete_user_image = AsyncMock(
            side_effect=ForgetImageForbiddenError()
        )

        action = ForgetImageAction(
            user_id=uuid.uuid4(),
            client_role=UserRole.USER,
            reference=image_data.name,
            architecture=image_data.architecture,
        )

        with pytest.raises(ForgetImageForbiddenError):
            await processors.forget_image.wait_for_complete(action)

    async def test_forget_image_not_found(
        self,
        processors: ImageProcessors,
        mock_admin_image_repository: MagicMock,
    ) -> None:
        """Forget non-existent image should raise ImageNotFound."""
        mock_admin_image_repository.soft_delete_image_force = AsyncMock(side_effect=ImageNotFound())

        action = ForgetImageAction(
            user_id=uuid.uuid4(),
            client_role=UserRole.SUPERADMIN,
            reference="non-existent-image",
            architecture="x86_64",
        )

        with pytest.raises(ImageNotFound):
            await processors.forget_image.wait_for_complete(action)


class TestForgetImageById:
    """Tests for ImageService.forget_image_by_id"""

    async def test_forget_image_by_id_as_superadmin_success(
        self,
        processors: ImageProcessors,
        mock_admin_image_repository: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Superadmin can forget any image by ID."""
        deleted_image = replace(image_data, status=ImageStatus.DELETED)
        mock_admin_image_repository.soft_delete_image_by_id_force = AsyncMock(
            return_value=deleted_image
        )

        action = ForgetImageByIdAction(
            user_id=uuid.uuid4(),
            client_role=UserRole.SUPERADMIN,
            image_id=image_data.id,
        )

        result = await processors.forget_image_by_id.wait_for_complete(action)

        assert result.image.status == ImageStatus.DELETED
        mock_admin_image_repository.soft_delete_image_by_id_force.assert_called_once_with(
            image_data.id
        )

    async def test_forget_image_by_id_as_user_forbidden(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Regular user cannot forget image they don't own."""
        mock_image_repository.soft_delete_image_by_id = AsyncMock(
            side_effect=ForgetImageForbiddenError()
        )

        action = ForgetImageByIdAction(
            user_id=uuid.uuid4(),
            client_role=UserRole.USER,
            image_id=image_data.id,
        )

        with pytest.raises(ForgetImageForbiddenError):
            await processors.forget_image_by_id.wait_for_complete(action)

    async def test_forget_image_by_id_not_found(
        self,
        processors: ImageProcessors,
        mock_admin_image_repository: MagicMock,
    ) -> None:
        """Forget non-existent image should raise ImageNotFound."""
        mock_admin_image_repository.soft_delete_image_by_id_force = AsyncMock(
            side_effect=ImageNotFound()
        )

        action = ForgetImageByIdAction(
            user_id=uuid.uuid4(),
            client_role=UserRole.SUPERADMIN,
            image_id=uuid.uuid4(),
        )

        with pytest.raises(ImageNotFound):
            await processors.forget_image_by_id.wait_for_complete(action)


class TestModifyImage:
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


class TestPurgeImageById:
    """Tests for ImageService.purge_image_by_id"""

    async def test_purge_image_by_id_as_superadmin_success(
        self,
        processors: ImageProcessors,
        mock_admin_image_repository: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Superadmin can purge any image by ID."""
        mock_admin_image_repository.delete_image_with_aliases_force = AsyncMock(
            return_value=image_data
        )

        action = PurgeImageByIdAction(
            user_id=uuid.uuid4(),
            client_role=UserRole.SUPERADMIN,
            image_id=image_data.id,
        )

        result = await processors.purge_image_by_id.wait_for_complete(action)

        assert result.image == image_data
        mock_admin_image_repository.delete_image_with_aliases_force.assert_called_once_with(
            image_data.id
        )

    async def test_purge_image_by_id_as_user_forbidden(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Regular user cannot purge image they don't own."""
        mock_image_repository.delete_image_with_aliases_validated = AsyncMock(
            side_effect=ForgetImageForbiddenError()
        )

        action = PurgeImageByIdAction(
            user_id=uuid.uuid4(),
            client_role=UserRole.USER,
            image_id=image_data.id,
        )

        with pytest.raises(ForgetImageForbiddenError):
            await processors.purge_image_by_id.wait_for_complete(action)

    async def test_purge_image_by_id_not_found(
        self,
        processors: ImageProcessors,
        mock_admin_image_repository: MagicMock,
    ) -> None:
        """Purge non-existent image should raise ImageNotFound."""
        mock_admin_image_repository.delete_image_with_aliases_force = AsyncMock(
            side_effect=ImageNotFound()
        )

        action = PurgeImageByIdAction(
            user_id=uuid.uuid4(),
            client_role=UserRole.SUPERADMIN,
            image_id=uuid.uuid4(),
        )

        with pytest.raises(ImageNotFound):
            await processors.purge_image_by_id.wait_for_complete(action)


class TestPurgeImages:
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


class TestUntagImageFromRegistry:
    """Tests for ImageService.untag_image_from_registry"""

    async def test_untag_image_as_superadmin_success(
        self,
        processors: ImageProcessors,
        mock_admin_image_repository: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Superadmin can untag any image from registry."""
        mock_admin_image_repository.untag_image_from_registry_force = AsyncMock(
            return_value=image_data
        )

        action = UntagImageFromRegistryAction(
            user_id=uuid.uuid4(),
            client_role=UserRole.SUPERADMIN,
            image_id=image_data.id,
        )

        result = await processors.untag_image_from_registry.wait_for_complete(action)

        assert result.image == image_data
        mock_admin_image_repository.untag_image_from_registry_force.assert_called_once_with(
            image_data.id
        )

    async def test_untag_image_as_user_forbidden(
        self,
        processors: ImageProcessors,
        mock_image_repository: MagicMock,
        image_data: ImageData,
    ) -> None:
        """Regular user cannot untag image they don't own."""
        mock_image_repository.untag_image_from_registry_validated = AsyncMock(
            side_effect=ForgetImageForbiddenError()
        )

        action = UntagImageFromRegistryAction(
            user_id=uuid.uuid4(),
            client_role=UserRole.USER,
            image_id=image_data.id,
        )

        with pytest.raises(ForgetImageForbiddenError):
            await processors.untag_image_from_registry.wait_for_complete(action)

    async def test_untag_image_not_found(
        self,
        processors: ImageProcessors,
        mock_admin_image_repository: MagicMock,
    ) -> None:
        """Untag non-existent image should raise ImageNotFound."""
        mock_admin_image_repository.untag_image_from_registry_force = AsyncMock(
            side_effect=ImageNotFound()
        )

        action = UntagImageFromRegistryAction(
            user_id=uuid.uuid4(),
            client_role=UserRole.SUPERADMIN,
            image_id=uuid.uuid4(),
        )

        with pytest.raises(ImageNotFound):
            await processors.untag_image_from_registry.wait_for_complete(action)


class TestClearImageCustomResourceLimit:
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
