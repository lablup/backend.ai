import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.exception import UnknownImageReference
from ai.backend.manager.data.image.types import (
    ImageAliasData,
    ImageData,
    ImageLabelsData,
    ImageResourcesData,
    ImageStatus,
    ImageType,
)
from ai.backend.manager.errors.image import ImageNotFound
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.image.admin_repository import AdminImageRepository
from ai.backend.manager.repositories.image.repository import ImageRepository
from ai.backend.manager.services.image.actions.alias_image import AliasImageAction
from ai.backend.manager.services.image.actions.clear_image_custom_resource_limit import (
    ClearImageCustomResourceLimitAction,
)
from ai.backend.manager.services.image.actions.dealias_image import DealiasImageAction
from ai.backend.manager.services.image.actions.forget_image import ForgetImageAction
from ai.backend.manager.services.image.actions.forget_image_by_id import ForgetImageByIdAction
from ai.backend.manager.services.image.actions.modify_image import (
    ImageModifier,
    ModifyImageAction,
    ModifyImageActionUnknownImageReferenceError,
)
from ai.backend.manager.services.image.actions.purge_image_by_id import PurgeImageByIdAction
from ai.backend.manager.services.image.actions.purge_images import (
    PurgeImageAction,
    PurgeImagesAction,
    PurgeImagesKeyData,
)
from ai.backend.manager.services.image.actions.scan_image import ScanImageAction
from ai.backend.manager.services.image.actions.untag_image_from_registry import (
    UntagImageFromRegistryAction,
)
from ai.backend.manager.services.image.service import ImageService
from ai.backend.manager.services.image.types import ImageRefData
from ai.backend.manager.types import OptionalState


def create_test_image_data(
    name: str = "test-image:latest",
    architecture: str = "x86_64",
    **kwargs,
) -> ImageData:
    """Helper function to create test ImageData with sensible defaults."""
    image_id = kwargs.get("id", uuid.uuid4())
    registry_id = kwargs.get("registry_id", uuid.uuid4())

    return ImageData(
        id=image_id,
        name=name,
        project=kwargs.get("project", "test-project"),
        image=kwargs.get("image", "test-image"),
        created_at=kwargs.get("created_at", datetime.now()),
        tag=kwargs.get("tag", "latest"),
        registry=kwargs.get("registry", "docker.io"),
        registry_id=registry_id,
        architecture=architecture,
        config_digest=kwargs.get("config_digest", "sha256:" + "0" * 64),
        size_bytes=kwargs.get("size_bytes", 1024 * 1024 * 100),
        is_local=kwargs.get("is_local", False),
        type=kwargs.get("type", ImageType.COMPUTE),
        accelerators=kwargs.get("accelerators", None),
        labels=kwargs.get("labels", ImageLabelsData(label_data={})),
        resources=kwargs.get("resources", ImageResourcesData(resources_data={})),
        status=kwargs.get("status", ImageStatus.ALIVE),
    )


@pytest.fixture
def mock_agent_registry() -> AgentRegistry:
    return MagicMock(spec=AgentRegistry)


@pytest.fixture
def mock_image_repository() -> ImageRepository:
    return MagicMock(spec=ImageRepository)


@pytest.fixture
def mock_admin_image_repository() -> AdminImageRepository:
    return MagicMock(spec=AdminImageRepository)


@pytest.fixture
def image_service(
    mock_agent_registry: AgentRegistry,
    mock_image_repository: ImageRepository,
    mock_admin_image_repository: AdminImageRepository,
) -> ImageService:
    return ImageService(
        agent_registry=mock_agent_registry,
        image_repository=mock_image_repository,
        admin_image_repository=mock_admin_image_repository,
    )


@pytest.mark.asyncio
async def test_forget_image_superadmin(
    image_service: ImageService,
    mock_admin_image_repository: AdminImageRepository,
) -> None:
    # Arrange
    user_id = uuid.uuid4()
    deleted_image = create_test_image_data(status=ImageStatus.DELETED)

    mock_admin_image_repository.soft_delete_image_force = AsyncMock(return_value=deleted_image)

    action = ForgetImageAction(
        reference="test-image:latest",
        architecture="x86_64",
        client_role=UserRole.SUPERADMIN,
        user_id=user_id,
    )

    # Act
    result = await image_service.forget_image(action)

    # Assert
    assert result.image == deleted_image
    assert result.image.status == ImageStatus.DELETED
    mock_admin_image_repository.soft_delete_image_force.assert_called_once()


@pytest.mark.asyncio
async def test_forget_image_regular_user(
    image_service: ImageService,
    mock_image_repository: ImageRepository,
) -> None:
    # Arrange
    user_id = uuid.uuid4()
    deleted_image = create_test_image_data(
        name="user-image:latest",
        status=ImageStatus.DELETED,
    )

    mock_image_repository.soft_delete_user_image = AsyncMock(return_value=deleted_image)

    action = ForgetImageAction(
        reference="user-image:latest",
        architecture="x86_64",
        client_role=UserRole.USER,
        user_id=user_id,
    )

    # Act
    result = await image_service.forget_image(action)

    # Assert
    assert result.image == deleted_image
    assert result.image.status == ImageStatus.DELETED
    mock_image_repository.soft_delete_user_image.assert_called_once_with(
        MagicMock,
        user_id,  # The identifiers list is a MagicMock, we just check user_id
    )


@pytest.mark.asyncio
async def test_forget_image_by_id_superadmin(
    image_service: ImageService,
    mock_admin_image_repository: AdminImageRepository,
) -> None:
    # Arrange
    image_id = uuid.uuid4()
    user_id = uuid.uuid4()
    deleted_image = create_test_image_data(id=image_id, status=ImageStatus.DELETED)

    mock_admin_image_repository.soft_delete_image_by_id_force = AsyncMock(
        return_value=deleted_image
    )

    action = ForgetImageByIdAction(
        image_id=image_id,
        client_role=UserRole.SUPERADMIN,
        user_id=user_id,
    )

    # Act
    result = await image_service.forget_image_by_id(action)

    # Assert
    assert result.image == deleted_image
    assert result.image.status == ImageStatus.DELETED
    mock_admin_image_repository.soft_delete_image_by_id_force.assert_called_once_with(image_id)


@pytest.mark.asyncio
async def test_forget_image_by_id_regular_user(
    image_service: ImageService,
    mock_image_repository: ImageRepository,
) -> None:
    # Arrange
    image_id = uuid.uuid4()
    user_id = uuid.uuid4()
    deleted_image = create_test_image_data(
        id=image_id,
        name="user-image:latest",
        status=ImageStatus.DELETED,
    )

    mock_image_repository.soft_delete_image_by_id = AsyncMock(return_value=deleted_image)

    action = ForgetImageByIdAction(
        image_id=image_id,
        client_role=UserRole.USER,
        user_id=user_id,
    )

    # Act
    result = await image_service.forget_image_by_id(action)

    # Assert
    assert result.image == deleted_image
    assert result.image.status == ImageStatus.DELETED
    mock_image_repository.soft_delete_image_by_id.assert_called_once_with(image_id, user_id)


@pytest.mark.asyncio
async def test_alias_image_success(
    image_service: ImageService,
    mock_image_repository: ImageRepository,
) -> None:
    # Arrange
    image_id = uuid.uuid4()
    alias_data = ImageAliasData(
        id=uuid.uuid4(),
        alias="my-alias",
    )

    mock_image_repository.add_image_alias = AsyncMock(return_value=(image_id, alias_data))

    action = AliasImageAction(
        alias="my-alias",
        image_canonical="test-image:latest",
        architecture="x86_64",
    )

    # Act
    result = await image_service.alias_image(action)

    # Assert
    assert result.image_id == image_id
    assert result.image_alias == alias_data
    mock_image_repository.add_image_alias.assert_called_once_with(
        "my-alias", "test-image:latest", "x86_64"
    )


@pytest.mark.asyncio
async def test_alias_image_unknown_reference(
    image_service: ImageService,
    mock_image_repository: ImageRepository,
) -> None:
    # Arrange
    mock_image_repository.add_image_alias = AsyncMock(
        side_effect=UnknownImageReference("Unknown image")
    )

    action = AliasImageAction(
        alias="my-alias",
        image_canonical="unknown-image:latest",
        architecture="x86_64",
    )

    # Act & Assert
    with pytest.raises(ImageNotFound):
        await image_service.alias_image(action)


@pytest.mark.asyncio
async def test_dealias_image(
    image_service: ImageService,
    mock_image_repository: ImageRepository,
) -> None:
    # Arrange
    image_id = uuid.uuid4()
    alias_data = ImageAliasData(
        id=uuid.uuid4(),
        alias="my-alias",
    )

    mock_image_repository.delete_image_alias = AsyncMock(return_value=(image_id, alias_data))

    action = DealiasImageAction(alias="my-alias")

    # Act
    result = await image_service.dealias_image(action)

    # Assert
    assert result.image_id == image_id
    assert result.image_alias == alias_data
    mock_image_repository.delete_image_alias.assert_called_once_with("my-alias")


@pytest.mark.asyncio
async def test_modify_image_success(
    image_service: ImageService,
    mock_image_repository: ImageRepository,
) -> None:
    # Arrange
    # Create image data with updated fields
    updated_labels = ImageLabelsData(label_data={"description": "Updated description"})
    updated_resources = ImageResourcesData(resources_data={"cpu": "2", "memory": "4g"})

    image_data = create_test_image_data(
        labels=updated_labels,
        resources=updated_resources,
    )

    mock_image_repository.update_image_properties = AsyncMock(return_value=image_data)

    modifier = ImageModifier(
        description=OptionalState.update("Updated description"),
        resource_limits=OptionalState.update({"cpu": "2", "memory": "4g"}),
    )
    action = ModifyImageAction(
        target="test-image:latest",
        architecture="x86_64",
        modifier=modifier,
    )

    # Act
    result = await image_service.modify_image(action)

    # Assert
    assert result.image == image_data
    mock_image_repository.update_image_properties.assert_called_once()

    # Verify the call arguments
    call_args = mock_image_repository.update_image_properties.call_args[0]
    assert call_args[0] == "test-image:latest"
    assert call_args[1] == "x86_64"
    assert "description" in call_args[2]
    assert "resource_limits" in call_args[2]


@pytest.mark.asyncio
async def test_modify_image_unknown_reference(
    image_service: ImageService,
    mock_image_repository: ImageRepository,
) -> None:
    # Arrange
    mock_image_repository.update_image_properties = AsyncMock(
        side_effect=UnknownImageReference("Unknown image")
    )

    modifier = ImageModifier(
        description=OptionalState.update("New description"),
    )
    action = ModifyImageAction(
        target="unknown-image:latest",
        architecture="x86_64",
        modifier=modifier,
    )

    # Act & Assert
    with pytest.raises(ModifyImageActionUnknownImageReferenceError):
        await image_service.modify_image(action)


@pytest.mark.asyncio
async def test_scan_image(
    image_service: ImageService,
    mock_image_repository: ImageRepository,
) -> None:
    # Arrange
    image_data = create_test_image_data()

    mock_image_repository.scan_image_by_identifier = AsyncMock(
        return_value=MagicMock(images=[image_data], errors=[])
    )

    action = ScanImageAction(
        canonical="test-image:latest",
        architecture="x86_64",
    )

    # Act
    result = await image_service.scan_image(action)

    # Assert
    assert result.image == image_data
    assert result.errors == []
    mock_image_repository.scan_image_by_identifier.assert_called_once_with(
        "test-image:latest", "x86_64"
    )


@pytest.mark.asyncio
async def test_clear_image_custom_resource_limit(
    image_service: ImageService,
    mock_image_repository: ImageRepository,
) -> None:
    # Arrange
    image_data = create_test_image_data(
        resources=ImageResourcesData(resources_data={}),
    )

    mock_image_repository.clear_image_custom_resource_limit = AsyncMock(return_value=image_data)

    action = ClearImageCustomResourceLimitAction(
        image_canonical="test-image:latest",
        architecture="x86_64",
    )

    # Act
    result = await image_service.clear_image_custom_resource_limit(action)

    # Assert
    assert result.image_data == image_data
    mock_image_repository.clear_image_custom_resource_limit.assert_called_once_with(
        "test-image:latest", "x86_64"
    )


@pytest.mark.asyncio
async def test_purge_image_by_id_superadmin(
    image_service: ImageService,
    mock_admin_image_repository: AdminImageRepository,
) -> None:
    # Arrange
    image_id = uuid.uuid4()
    user_id = uuid.uuid4()
    deleted_image = create_test_image_data(id=image_id)

    mock_admin_image_repository.delete_image_with_aliases_force = AsyncMock(
        return_value=deleted_image
    )

    action = PurgeImageByIdAction(
        image_id=image_id,
        client_role=UserRole.SUPERADMIN,
        user_id=user_id,
    )

    # Act
    result = await image_service.purge_image_by_id(action)

    # Assert
    assert result.image == deleted_image
    mock_admin_image_repository.delete_image_with_aliases_force.assert_called_once_with(image_id)


@pytest.mark.asyncio
async def test_purge_image_by_id_regular_user(
    image_service: ImageService,
    mock_image_repository: ImageRepository,
) -> None:
    # Arrange
    image_id = uuid.uuid4()
    user_id = uuid.uuid4()
    deleted_image = create_test_image_data(id=image_id)

    mock_image_repository.delete_image_with_aliases_validated = AsyncMock(
        return_value=deleted_image
    )

    action = PurgeImageByIdAction(
        image_id=image_id,
        client_role=UserRole.USER,
        user_id=user_id,
    )

    # Act
    result = await image_service.purge_image_by_id(action)

    # Assert
    assert result.image == deleted_image
    mock_image_repository.delete_image_with_aliases_validated.assert_called_once_with(
        image_id, user_id
    )


@pytest.mark.asyncio
async def test_untag_image_from_registry_superadmin(
    image_service: ImageService,
    mock_admin_image_repository: AdminImageRepository,
) -> None:
    # Arrange
    image_id = uuid.uuid4()
    user_id = uuid.uuid4()
    image_data = create_test_image_data(id=image_id)

    mock_admin_image_repository.untag_image_from_registry_force = AsyncMock(return_value=image_data)

    action = UntagImageFromRegistryAction(
        image_id=image_id,
        client_role=UserRole.SUPERADMIN,
        user_id=user_id,
    )

    # Act
    result = await image_service.untag_image_from_registry(action)

    # Assert
    assert result.image == image_data
    mock_admin_image_repository.untag_image_from_registry_force.assert_called_once_with(image_id)


@pytest.mark.asyncio
async def test_untag_image_from_registry_regular_user(
    image_service: ImageService,
    mock_image_repository: ImageRepository,
) -> None:
    # Arrange
    image_id = uuid.uuid4()
    user_id = uuid.uuid4()
    image_data = create_test_image_data(id=image_id)

    mock_image_repository.untag_image_from_registry_validated = AsyncMock(return_value=image_data)

    action = UntagImageFromRegistryAction(
        image_id=image_id,
        client_role=UserRole.USER,
        user_id=user_id,
    )

    # Act
    result = await image_service.untag_image_from_registry(action)

    # Assert
    assert result.image == image_data
    mock_image_repository.untag_image_from_registry_validated.assert_called_once_with(
        image_id, user_id
    )


@pytest.mark.asyncio
async def test_purge_image(
    image_service: ImageService,
    mock_agent_registry: AgentRegistry,
    mock_image_repository: ImageRepository,
) -> None:
    # Arrange
    agent_id = "agent-1"
    image_data = create_test_image_data(name="test-image:latest")

    mock_image_repository.resolve_image = AsyncMock(return_value=image_data)
    mock_agent_registry.purge_images = AsyncMock(
        return_value=MagicMock(responses=[MagicMock(image="test-image:latest", error=None)])
    )

    action = PurgeImageAction(
        agent_id=agent_id,
        image=ImageRefData(name="test-image:latest", architecture="x86_64"),
        force=True,
        noprune=False,
    )

    # Act
    result = await image_service.purge_image(action)

    # Assert
    assert result.purged_image == image_data
    assert result.error is None
    assert result.reserved_bytes == image_data.size_bytes
    mock_agent_registry.purge_images.assert_called_once()


@pytest.mark.asyncio
async def test_purge_image_with_error(
    image_service: ImageService,
    mock_agent_registry: AgentRegistry,
    mock_image_repository: ImageRepository,
) -> None:
    # Arrange
    agent_id = "agent-1"
    image_data = create_test_image_data(name="test-image:latest")
    error_msg = "Failed to purge: image in use"

    mock_image_repository.resolve_image = AsyncMock(return_value=image_data)
    mock_agent_registry.purge_images = AsyncMock(
        return_value=MagicMock(responses=[MagicMock(image="test-image:latest", error=error_msg)])
    )

    action = PurgeImageAction(
        agent_id=agent_id,
        image=ImageRefData(name="test-image:latest", architecture="x86_64"),
        force=True,
        noprune=False,
    )

    # Act
    result = await image_service.purge_image(action)

    # Assert
    assert result.purged_image == image_data
    assert error_msg in result.error
    assert result.reserved_bytes == image_data.size_bytes


@pytest.mark.asyncio
async def test_purge_images_success(
    image_service: ImageService,
    mock_agent_registry: AgentRegistry,
    mock_image_repository: ImageRepository,
) -> None:
    # Arrange
    image1 = create_test_image_data(name="image1:latest", size_bytes=100 * 1024 * 1024)
    image2 = create_test_image_data(name="image2:latest", size_bytes=200 * 1024 * 1024)

    mock_agent_registry.purge_images = AsyncMock(
        return_value=MagicMock(
            responses=[
                MagicMock(image="image1:latest", error=None),
                MagicMock(image="image2:latest", error=None),
            ]
        )
    )
    mock_image_repository.resolve_images_batch = AsyncMock(return_value=[image1, image2])

    action = PurgeImagesAction(
        keys=[
            PurgeImagesKeyData(
                agent_id="agent-1",
                images=[
                    ImageRefData(name="image1:latest", architecture="x86_64"),
                    ImageRefData(name="image2:latest", architecture="x86_64"),
                ],
            )
        ],
        force=True,
        noprune=False,
    )

    # Act
    result = await image_service.purge_images(action)

    # Assert
    assert len(result.purged_images) == 1
    assert result.purged_images[0].agent_id == "agent-1"
    assert len(result.purged_images[0].purged_images) == 2
    assert result.errors == []
    assert result.total_reserved_bytes == 300 * 1024 * 1024


@pytest.mark.asyncio
async def test_purge_images_partial_failure(
    image_service: ImageService,
    mock_agent_registry: AgentRegistry,
    mock_image_repository: ImageRepository,
) -> None:
    # Arrange
    image1 = create_test_image_data(name="image1:latest", size_bytes=100 * 1024 * 1024)

    mock_agent_registry.purge_images = AsyncMock(
        return_value=MagicMock(
            responses=[
                MagicMock(image="image1:latest", error=None),
                MagicMock(image="image2:latest", error="Image in use"),
            ]
        )
    )
    mock_image_repository.resolve_images_batch = AsyncMock(
        return_value=[image1]  # Only image1 was successfully purged
    )

    action = PurgeImagesAction(
        keys=[
            PurgeImagesKeyData(
                agent_id="agent-1",
                images=[
                    ImageRefData(name="image1:latest", architecture="x86_64"),
                    ImageRefData(name="image2:latest", architecture="x86_64"),
                ],
            )
        ],
        force=True,
        noprune=False,
    )

    # Act
    result = await image_service.purge_images(action)

    # Assert
    assert len(result.purged_images) == 1
    assert len(result.purged_images[0].purged_images) == 1
    assert len(result.errors) == 1
    assert "Image in use" in result.errors[0]
    assert result.total_reserved_bytes == 100 * 1024 * 1024


@pytest.mark.asyncio
async def test_purge_images_multiple_agents(
    image_service: ImageService,
    mock_agent_registry: AgentRegistry,
    mock_image_repository: ImageRepository,
) -> None:
    # Arrange
    image1 = create_test_image_data(name="image1:latest", size_bytes=100 * 1024 * 1024)

    # Mock responses for two different agents
    mock_agent_registry.purge_images = AsyncMock(
        side_effect=[
            MagicMock(responses=[MagicMock(image="image1:latest", error=None)]),
            MagicMock(responses=[MagicMock(image="image1:latest", error=None)]),
        ]
    )
    mock_image_repository.resolve_images_batch = AsyncMock(side_effect=[[image1], [image1]])

    action = PurgeImagesAction(
        keys=[
            PurgeImagesKeyData(
                agent_id="agent-1",
                images=[ImageRefData(name="image1:latest", architecture="x86_64")],
            ),
            PurgeImagesKeyData(
                agent_id="agent-2",
                images=[ImageRefData(name="image1:latest", architecture="x86_64")],
            ),
        ],
        force=True,
        noprune=False,
    )

    # Act
    result = await image_service.purge_images(action)

    # Assert
    assert len(result.purged_images) == 2
    assert result.purged_images[0].agent_id == "agent-1"
    assert result.purged_images[1].agent_id == "agent-2"
    assert result.errors == []
    assert result.total_reserved_bytes == 200 * 1024 * 1024  # Same image purged from 2 agents
