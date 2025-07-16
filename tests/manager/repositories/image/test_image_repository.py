import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.exception import UnknownImageReference
from ai.backend.common.types import ImageAlias
from ai.backend.manager.data.image.types import (
    ImageAliasData,
    ImageData,
    ImageLabelsData,
    ImageResourcesData,
    ImageStatus,
    ImageType,
)
from ai.backend.manager.errors.image import (
    ForgetImageForbiddenError,
    ForgetImageNotFoundError,
    ImageAliasNotFound,
)
from ai.backend.manager.models.image import ImageAliasRow, ImageIdentifier, ImageRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.image.repository import ImageRepository


def create_test_image_row(**kwargs) -> ImageRow:
    """Helper function to create test ImageRow with sensible defaults."""
    row = MagicMock(spec=ImageRow)
    row.id = kwargs.get("id", uuid.uuid4())
    row.name = kwargs.get("name", "test-image:latest")
    row.architecture = kwargs.get("architecture", "x86_64")
    row.is_deleted = kwargs.get("is_deleted", False)
    row.to_dataclass = MagicMock(return_value=create_test_image_data(**kwargs))
    return row


def create_test_image_data(**kwargs) -> ImageData:
    """Helper function to create test ImageData with sensible defaults."""
    image_id = kwargs.get("id", uuid.uuid4())
    registry_id = kwargs.get("registry_id", uuid.uuid4())
    
    return ImageData(
        id=image_id,
        name=kwargs.get("name", "test-image:latest"),
        project=kwargs.get("project", "test-project"),
        image=kwargs.get("image", "test-image"),
        created_at=kwargs.get("created_at", datetime.now()),
        tag=kwargs.get("tag", "latest"),
        registry=kwargs.get("registry", "docker.io"),
        registry_id=registry_id,
        architecture=kwargs.get("architecture", "x86_64"),
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
def mock_db_engine() -> ExtendedAsyncSAEngine:
    db = MagicMock(spec=ExtendedAsyncSAEngine)
    return db


@pytest.fixture
def image_repository(mock_db_engine: ExtendedAsyncSAEngine) -> ImageRepository:
    return ImageRepository(db=mock_db_engine)


@pytest.mark.asyncio
async def test_resolve_image(
    image_repository: ImageRepository,
    mock_db_engine: ExtendedAsyncSAEngine,
) -> None:
    # Arrange
    test_image_row = create_test_image_row()
    
    mock_session = AsyncMock()
    mock_db_engine.begin_session = AsyncMock(return_value=mock_session)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch.object(image_repository, "_resolve_image", AsyncMock(return_value=test_image_row)):
        # Act
        result = await image_repository.resolve_image([ImageIdentifier("test-image:latest", "x86_64")])
        
        # Assert
        assert result.id == test_image_row.id
        assert result.name == test_image_row.name
        assert result.architecture == test_image_row.architecture


@pytest.mark.asyncio
async def test_resolve_images_batch(
    image_repository: ImageRepository,
    mock_db_engine: ExtendedAsyncSAEngine,
) -> None:
    # Arrange
    test_rows = [
        create_test_image_row(name="image1:latest"),
        create_test_image_row(name="image2:latest"),
    ]
    
    mock_session = AsyncMock()
    mock_db_engine.begin_session = AsyncMock(return_value=mock_session)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch.object(image_repository, "_resolve_image", AsyncMock(side_effect=test_rows)):
        # Act
        identifier_lists = [
            [ImageIdentifier("image1:latest", "x86_64")],
            [ImageIdentifier("image2:latest", "x86_64")],
        ]
        result = await image_repository.resolve_images_batch(identifier_lists)
        
        # Assert
        assert len(result) == 2
        assert result[0].name == "image1:latest"
        assert result[1].name == "image2:latest"


@pytest.mark.asyncio
async def test_soft_delete_user_image_success(
    image_repository: ImageRepository,
    mock_db_engine: ExtendedAsyncSAEngine,
) -> None:
    # Arrange
    user_id = uuid.uuid4()
    image_id = uuid.uuid4()
    test_image_row = create_test_image_row(id=image_id, owner_user_id=user_id)
    test_image_row.is_owned_by = MagicMock(return_value=True)
    test_image_row.mark_as_deleted = AsyncMock()
    
    mock_session = AsyncMock()
    mock_db_engine.begin_session = AsyncMock(return_value=mock_session)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch.object(image_repository, "_resolve_image", AsyncMock(return_value=test_image_row)):
        # Act
        result = await image_repository.soft_delete_user_image(
            [ImageIdentifier("test-image:latest", "x86_64")],
            user_id,
        )
        
        # Assert
        assert result.id == image_id
        test_image_row.is_owned_by.assert_called_once_with(user_id)
        test_image_row.mark_as_deleted.assert_called_once_with(mock_session)


@pytest.mark.asyncio
async def test_soft_delete_user_image_forbidden(
    image_repository: ImageRepository,
    mock_db_engine: ExtendedAsyncSAEngine,
) -> None:
    # Arrange
    user_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    test_image_row = create_test_image_row(owner_user_id=other_user_id)
    test_image_row.is_owned_by = MagicMock(return_value=False)
    
    mock_session = AsyncMock()
    mock_db_engine.begin_session = AsyncMock(return_value=mock_session)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch.object(image_repository, "_resolve_image", AsyncMock(return_value=test_image_row)):
        # Act & Assert
        with pytest.raises(ForgetImageForbiddenError):
            await image_repository.soft_delete_user_image(
                [ImageIdentifier("test-image:latest", "x86_64")],
                user_id,
            )


@pytest.mark.asyncio
async def test_add_image_alias_success(
    image_repository: ImageRepository,
    mock_db_engine: ExtendedAsyncSAEngine,
) -> None:
    # Arrange
    image_id = uuid.uuid4()
    alias_id = uuid.uuid4()
    test_image_row = create_test_image_row(id=image_id)
    
    mock_alias_row = MagicMock(spec=ImageAliasRow)
    mock_alias_row.id = alias_id
    mock_alias_row.alias = "my-alias"
    mock_alias_row.image_id = image_id
    mock_alias_row.to_dataclass = MagicMock(
        return_value=ImageAliasData(id=alias_id, alias="my-alias")
    )
    
    test_image_row.aliases = MagicMock()
    test_image_row.aliases.append = MagicMock()
    
    mock_session = AsyncMock()
    mock_db_engine.begin_session = AsyncMock(return_value=mock_session)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch.object(image_repository, "_resolve_image", AsyncMock(return_value=test_image_row)):
        with patch("ai.backend.manager.models.image.ImageAliasRow", return_value=mock_alias_row):
            # Act
            result_id, result_alias = await image_repository.add_image_alias(
                "my-alias", "test-image:latest", "x86_64"
            )
            
            # Assert
            assert result_id == image_id
            assert result_alias.alias == "my-alias"


@pytest.mark.asyncio
async def test_add_image_alias_unknown_image(
    image_repository: ImageRepository,
    mock_db_engine: ExtendedAsyncSAEngine,
) -> None:
    # Arrange
    mock_session = AsyncMock()
    mock_db_engine.begin_session = AsyncMock(return_value=mock_session)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch.object(
        image_repository,
        "_resolve_image",
        AsyncMock(side_effect=UnknownImageReference("Unknown image")),
    ):
        # Act & Assert
        with pytest.raises(UnknownImageReference):
            await image_repository.add_image_alias(
                "my-alias", "unknown-image:latest", "x86_64"
            )


@pytest.mark.asyncio
async def test_delete_image_alias_success(
    image_repository: ImageRepository,
    mock_db_engine: ExtendedAsyncSAEngine,
) -> None:
    # Arrange
    image_id = uuid.uuid4()
    alias_id = uuid.uuid4()
    
    mock_alias_row = MagicMock(spec=ImageAliasRow)
    mock_alias_row.image_id = image_id
    mock_alias_row.to_dataclass = MagicMock(
        return_value=ImageAliasData(id=alias_id, alias="my-alias")
    )
    
    mock_session = AsyncMock()
    mock_session.scalar = AsyncMock(return_value=mock_alias_row)
    mock_session.delete = AsyncMock()
    
    mock_db_engine.begin_session = AsyncMock(return_value=mock_session)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    # Act
    result_id, result_alias = await image_repository.delete_image_alias("my-alias")
    
    # Assert
    assert result_id == image_id
    assert result_alias.alias == "my-alias"
    mock_session.delete.assert_called_once_with(mock_alias_row)


@pytest.mark.asyncio
async def test_delete_image_alias_not_found(
    image_repository: ImageRepository,
    mock_db_engine: ExtendedAsyncSAEngine,
) -> None:
    # Arrange
    mock_session = AsyncMock()
    mock_session.scalar = AsyncMock(return_value=None)
    
    mock_db_engine.begin_session = AsyncMock(return_value=mock_session)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    # Act & Assert
    with pytest.raises(ImageAliasNotFound):
        await image_repository.delete_image_alias("non-existent-alias")


@pytest.mark.asyncio
async def test_update_image_properties(
    image_repository: ImageRepository,
    mock_db_engine: ExtendedAsyncSAEngine,
) -> None:
    # Arrange
    image_id = uuid.uuid4()
    test_image_row = create_test_image_row(id=image_id)
    
    to_update = {
        "description": "Updated description",
        "resource_limits": {"cpu": "2", "memory": "4g"},
    }
    
    # Mock setattr to track updates
    original_setattr = setattr
    setattr_calls = []
    
    def mock_setattr(obj, name, value):
        if obj == test_image_row:
            setattr_calls.append((name, value))
        original_setattr(obj, name, value)
    
    mock_session = AsyncMock()
    mock_db_engine.begin_session = AsyncMock(return_value=mock_session)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch.object(image_repository, "_resolve_image", AsyncMock(return_value=test_image_row)):
        with patch("builtins.setattr", side_effect=mock_setattr):
            # Act
            result = await image_repository.update_image_properties(
                "test-image:latest", "x86_64", to_update
            )
            
            # Assert
            assert result.id == image_id
            assert len(setattr_calls) == 2
            assert ("description", "Updated description") in setattr_calls
            assert ("resource_limits", {"cpu": "2", "memory": "4g"}) in setattr_calls


@pytest.mark.asyncio
async def test_soft_delete_image_by_id(
    image_repository: ImageRepository,
    mock_db_engine: ExtendedAsyncSAEngine,
) -> None:
    # Arrange
    image_id = uuid.uuid4()
    user_id = uuid.uuid4()
    test_image_row = create_test_image_row(id=image_id, owner_user_id=user_id)
    test_image_row.is_owned_by = MagicMock(return_value=True)
    test_image_row.mark_as_deleted = AsyncMock()
    
    mock_session = AsyncMock()
    mock_session.get = AsyncMock(return_value=test_image_row)
    mock_db_engine.begin_session = AsyncMock(return_value=mock_session)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    # Act
    result = await image_repository.soft_delete_image_by_id(image_id, user_id)
    
    # Assert
    assert result.id == image_id
    test_image_row.is_owned_by.assert_called_once_with(user_id)
    test_image_row.mark_as_deleted.assert_called_once_with(mock_session)


@pytest.mark.asyncio
async def test_soft_delete_image_by_id_not_found(
    image_repository: ImageRepository,
    mock_db_engine: ExtendedAsyncSAEngine,
) -> None:
    # Arrange
    image_id = uuid.uuid4()
    user_id = uuid.uuid4()
    
    mock_session = AsyncMock()
    mock_session.get = AsyncMock(return_value=None)
    mock_db_engine.begin_session = AsyncMock(return_value=mock_session)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    # Act & Assert
    with pytest.raises(ForgetImageNotFoundError):
        await image_repository.soft_delete_image_by_id(image_id, user_id)


@pytest.mark.asyncio
async def test_delete_image_with_aliases_validated(
    image_repository: ImageRepository,
    mock_db_engine: ExtendedAsyncSAEngine,
) -> None:
    # Arrange
    image_id = uuid.uuid4()
    user_id = uuid.uuid4()
    test_image_row = create_test_image_row(id=image_id, owner_user_id=user_id)
    test_image_row.is_owned_by = MagicMock(return_value=True)
    
    # Mock aliases
    alias1 = MagicMock(spec=ImageAliasRow, id=uuid.uuid4(), alias="alias1")
    alias2 = MagicMock(spec=ImageAliasRow, id=uuid.uuid4(), alias="alias2")
    test_image_row.aliases = [alias1, alias2]
    
    mock_session = AsyncMock()
    mock_session.get = AsyncMock(return_value=test_image_row)
    mock_session.delete = AsyncMock()
    
    mock_db_engine.begin_session = AsyncMock(return_value=mock_session)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    # Act
    result = await image_repository.delete_image_with_aliases_validated(image_id, user_id)
    
    # Assert
    assert result.id == image_id
    # Should delete image and both aliases
    assert mock_session.delete.call_count == 3


@pytest.mark.asyncio
async def test_scan_image_by_identifier(
    image_repository: ImageRepository,
    mock_db_engine: ExtendedAsyncSAEngine,
) -> None:
    # Arrange
    canonical = "test-image:latest"
    architecture = "x86_64"
    
    mock_scan_result = MagicMock()
    mock_scan_result.images = [create_test_image_data()]
    mock_scan_result.errors = []
    
    mock_session = AsyncMock()
    mock_db_engine.begin_session = AsyncMock(return_value=mock_session)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch("ai.backend.manager.models.image.scan_single_image", AsyncMock(return_value=mock_scan_result)):
        # Act
        result = await image_repository.scan_image_by_identifier(canonical, architecture)
        
        # Assert
        assert result == mock_scan_result
        assert len(result.images) == 1
        assert result.errors == []


@pytest.mark.asyncio
async def test_clear_image_custom_resource_limit(
    image_repository: ImageRepository,
    mock_db_engine: ExtendedAsyncSAEngine,
) -> None:
    # Arrange
    image_id = uuid.uuid4()
    test_image_row = create_test_image_row(id=image_id)
    test_image_row.resource_limits = None  # Cleared
    
    mock_session = AsyncMock()
    mock_db_engine.begin_session = AsyncMock(return_value=mock_session)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch.object(image_repository, "_resolve_image", AsyncMock(return_value=test_image_row)):
        # Act
        result = await image_repository.clear_image_custom_resource_limit(
            "test-image:latest", "x86_64"
        )
        
        # Assert
        assert result.id == image_id
        # resource_limits should be cleared (None)
        assert getattr(test_image_row, "resource_limits", None) is None


@pytest.mark.asyncio
async def test_untag_image_from_registry_validated(
    image_repository: ImageRepository,
    mock_db_engine: ExtendedAsyncSAEngine,
) -> None:
    # Arrange
    image_id = uuid.uuid4()
    user_id = uuid.uuid4()
    test_image_row = create_test_image_row(id=image_id, owner_user_id=user_id)
    test_image_row.is_owned_by = MagicMock(return_value=True)
    test_image_row.registry = "docker.io"
    test_image_row.name = "test-image:latest"
    
    mock_session = AsyncMock()
    mock_session.get = AsyncMock(return_value=test_image_row)
    mock_db_engine.begin_session = AsyncMock(return_value=mock_session)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    # Mock registry client
    mock_registry_client = AsyncMock()
    mock_registry_client.untag_image = AsyncMock()
    
    with patch("ai.backend.manager.repositories.image.repository.get_registry_client", return_value=mock_registry_client):
        # Act
        result = await image_repository.untag_image_from_registry_validated(image_id, user_id)
        
        # Assert
        assert result.id == image_id
        mock_registry_client.untag_image.assert_called_once()


@pytest.mark.asyncio
async def test_untag_image_from_registry_unauthorized(
    image_repository: ImageRepository,
    mock_db_engine: ExtendedAsyncSAEngine,
) -> None:
    # Arrange
    image_id = uuid.uuid4()
    user_id = uuid.uuid4()
    different_user_id = uuid.uuid4()
    test_image_row = create_test_image_row(id=image_id, owner_user_id=different_user_id)
    test_image_row.is_owned_by = MagicMock(return_value=False)
    
    mock_session = AsyncMock()
    mock_session.get = AsyncMock(return_value=test_image_row)
    mock_db_engine.begin_session = AsyncMock(return_value=mock_session)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    # Act & Assert
    with pytest.raises(ForgetImageForbiddenError):
        await image_repository.untag_image_from_registry_validated(image_id, user_id)