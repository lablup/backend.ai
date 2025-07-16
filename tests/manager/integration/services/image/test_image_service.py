import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import sqlalchemy as sa

from ai.backend.common.dto.manager.rpc_request import PurgeImagesReq
from ai.backend.common.exception import UnknownImageReference
from ai.backend.common.types import ImageAlias
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.errors.exceptions import ImageNotFound
from ai.backend.manager.models.image import ImageIdentifier, ImageRow, ImageAliasRow
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.image.admin_repository import AdminImageRepository
from ai.backend.manager.repositories.image.repository import ImageRepository
from ai.backend.manager.services.image.actions.alias_image import (
    AliasImageAction,
    AliasImageActionResult,
)
from ai.backend.manager.services.image.actions.clear_image_custom_resource_limit import (
    ClearImageCustomResourceLimitAction,
    ClearImageCustomResourceLimitActionResult,
)
from ai.backend.manager.services.image.actions.dealias_image import (
    DealiasImageAction,
    DealiasImageActionResult,
)
from ai.backend.manager.services.image.actions.forget_image import (
    ForgetImageAction,
    ForgetImageActionResult,
)
from ai.backend.manager.services.image.actions.forget_image_by_id import (
    ForgetImageByIdAction,
    ForgetImageByIdActionResult,
)
from ai.backend.manager.services.image.actions.modify_image import (
    ModifyImageAction,
    ModifyImageActionResult,
    ImageModifier,
)
from ai.backend.manager.services.image.actions.purge_image_by_id import (
    PurgeImageByIdAction,
    PurgeImageByIdActionResult,
)
from ai.backend.manager.services.image.actions.purge_images import (
    PurgeImagesAction,
    PurgeImagesActionResult,
    PurgeImagesKeyData,
)
from ai.backend.manager.services.image.types import ImageRefData
from ai.backend.manager.services.image.actions.scan_image import (
    ScanImageAction,
    ScanImageActionResult,
)
from ai.backend.manager.services.image.actions.untag_image_from_registry import (
    UntagImageFromRegistryAction,
    UntagImageFromRegistryActionResult,
)
from ai.backend.manager.services.image.service import ImageService


@pytest.fixture
async def mock_agent_registry() -> AgentRegistry:
    """Mock AgentRegistry for testing."""
    mock_registry = MagicMock(spec=AgentRegistry)
    mock_registry.purge_images = AsyncMock()
    return mock_registry


@pytest.fixture
async def mock_image_repository(database_engine: ExtendedAsyncSAEngine) -> ImageRepository:
    """Mock ImageRepository for testing."""
    return ImageRepository(db=database_engine)


@pytest.fixture
async def mock_admin_image_repository(database_engine: ExtendedAsyncSAEngine) -> AdminImageRepository:
    """Mock AdminImageRepository for testing."""
    return AdminImageRepository(db=database_engine)


@pytest.fixture
async def image_service(
    mock_agent_registry: AgentRegistry,
    mock_image_repository: ImageRepository,
    mock_admin_image_repository: AdminImageRepository,
) -> ImageService:
    """Create ImageService instance for testing."""
    return ImageService(
        agent_registry=mock_agent_registry,
        image_repository=mock_image_repository,
        admin_image_repository=mock_admin_image_repository,
    )


@pytest.fixture
async def create_test_image(database_engine: ExtendedAsyncSAEngine):
    """Fixture to create test images in the database."""
    @asynccontextmanager
    async def _create_image(
        name: str = "test-image:latest",
        architecture: str = "x86_64",
        is_active: bool = True,
        owner_email: str = "test@example.com",
    ) -> AsyncGenerator[ImageRow, None]:
        async with database_engine.begin_session() as session:
            image_row = ImageRow(
                id=uuid.uuid4(),
                name=name,
                registry="docker.io",
                architecture=architecture,
                is_active=is_active,
                size_bytes=1024 * 1024 * 100,  # 100MB
                owner_email=owner_email,
                created_at=datetime.utcnow(),
            )
            session.add(image_row)
            await session.commit()
            yield image_row
            
            # Cleanup
            await session.execute(
                sa.delete(ImageRow).where(ImageRow.id == image_row.id)
            )
            await session.commit()
    
    return _create_image


@pytest.fixture
async def create_test_alias(database_engine: ExtendedAsyncSAEngine):
    """Fixture to create test image aliases in the database."""
    @asynccontextmanager
    async def _create_alias(
        alias: str,
        target_image_id: uuid.UUID,
    ) -> AsyncGenerator[ImageAliasRow, None]:
        async with database_engine.begin_session() as session:
            alias_row = ImageAliasRow(
                id=uuid.uuid4(),
                alias=alias,
                target=target_image_id,
                created_at=datetime.utcnow(),
            )
            session.add(alias_row)
            await session.commit()
            yield alias_row
            
            # Cleanup
            await session.execute(
                sa.delete(ImageAliasRow).where(ImageAliasRow.id == alias_row.id)
            )
            await session.commit()
    
    return _create_alias


class TestForgetImage:
    """Test cases for forget_image functionality."""
    
    async def test_forget_image_success_as_superadmin(
        self,
        image_service: ImageService,
        create_test_image,
        database_engine: ExtendedAsyncSAEngine,
    ) -> None:
        """Test successful image soft delete by superadmin."""
        async with create_test_image(name="ubuntu:20.04") as image:
            action = ForgetImageAction(
                user_id=uuid.uuid4(),
                client_role=UserRole.SUPERADMIN,
                reference="ubuntu:20.04",
                architecture="x86_64",
            )
            
            result = await image_service.forget_image(action)
            
            assert isinstance(result, ForgetImageActionResult)
            assert result.image.id == image.id
            assert result.image.name == "ubuntu:20.04"
            
            # Verify image is soft deleted
            async with database_engine.begin_session() as session:
                updated_image = await session.get(ImageRow, image.id)
                assert updated_image.is_active is False
    
    async def test_forget_image_by_alias(
        self,
        image_service: ImageService,
        create_test_image,
        create_test_alias,
        database_engine: ExtendedAsyncSAEngine,
    ) -> None:
        """Test forgetting image using alias."""
        async with create_test_image(name="ubuntu:20.04") as image:
            async with create_test_alias(alias="my-ubuntu", target_image_id=image.id):
                action = ForgetImageAction(
                    user_id=uuid.uuid4(),
                    client_role=UserRole.SUPERADMIN,
                    reference="my-ubuntu",
                    architecture="x86_64",
                )
                
                result = await image_service.forget_image(action)
                
                assert isinstance(result, ForgetImageActionResult)
                assert result.image.id == image.id
                
                # Verify original image is soft deleted
                async with database_engine.begin_session() as session:
                    updated_image = await session.get(ImageRow, image.id)
                    assert updated_image.is_active is False
    
    async def test_forget_non_existent_image(
        self,
        image_service: ImageService,
    ) -> None:
        """Test forgetting non-existent image."""
        action = ForgetImageAction(
            user_id=uuid.uuid4(),
            client_role=UserRole.SUPERADMIN,
            reference="non-existent:latest",
            architecture="x86_64",
        )
        
        with pytest.raises(ImageNotFound):
            await image_service.forget_image(action)
    
    async def test_forget_image_as_regular_user_owner(
        self,
        image_service: ImageService,
        create_test_image,
        database_engine: ExtendedAsyncSAEngine,
    ) -> None:
        """Test regular user can forget their own image."""
        user_id = uuid.uuid4()
        user_email = f"user-{user_id}@example.com"
        
        async with create_test_image(name="my-image:latest", owner_email=user_email) as image:
            action = ForgetImageAction(
                user_id=user_id,
                client_role=UserRole.USER,
                reference="my-image:latest",
                architecture="x86_64",
            )
            
            result = await image_service.forget_image(action)
            
            assert isinstance(result, ForgetImageActionResult)
            assert result.image.id == image.id
            
            # Verify image is soft deleted
            async with database_engine.begin_session() as session:
                updated_image = await session.get(ImageRow, image.id)
                assert updated_image.is_active is False
    
    async def test_forget_image_as_regular_user_not_owner(
        self,
        image_service: ImageService,
        create_test_image,
    ) -> None:
        """Test regular user cannot forget image they don't own."""
        async with create_test_image(name="other-image:latest", owner_email="other@example.com"):
            action = ForgetImageAction(
                user_id=uuid.uuid4(),
                client_role=UserRole.USER,
                reference="other-image:latest",
                architecture="x86_64",
            )
            
            with pytest.raises(ImageNotFound):
                await image_service.forget_image(action)


class TestForgetImageById:
    """Test cases for forget_image_by_id functionality."""
    
    async def test_forget_image_by_id_success(
        self,
        image_service: ImageService,
        create_test_image,
        database_engine: ExtendedAsyncSAEngine,
    ) -> None:
        """Test successful image soft delete by ID."""
        async with create_test_image() as image:
            action = ForgetImageByIdAction(
                user_id=uuid.uuid4(),
                client_role=UserRole.SUPERADMIN,
                image_id=image.id,
            )
            
            result = await image_service.forget_image_by_id(action)
            
            assert isinstance(result, ForgetImageByIdActionResult)
            assert result.image.id == image.id
            
            # Verify image is soft deleted
            async with database_engine.begin_session() as session:
                updated_image = await session.get(ImageRow, image.id)
                assert updated_image.is_active is False
    
    async def test_forget_image_by_invalid_id(
        self,
        image_service: ImageService,
    ) -> None:
        """Test forgetting image with invalid UUID."""
        action = ForgetImageByIdAction(
            user_id=uuid.uuid4(),
            client_role=UserRole.SUPERADMIN,
            image_id=uuid.uuid4(),  # Non-existent ID
        )
        
        with pytest.raises(ImageNotFound):
            await image_service.forget_image_by_id(action)


class TestPurgeImageById:
    """Test cases for purge_image_by_id functionality."""
    
    async def test_purge_image_by_id_success(
        self,
        image_service: ImageService,
        create_test_image,
        database_engine: ExtendedAsyncSAEngine,
    ) -> None:
        """Test successful image hard delete."""
        async with create_test_image() as image:
            image_id = image.id
            action = PurgeImageByIdAction(
                user_id=uuid.uuid4(),
                client_role=UserRole.SUPERADMIN,
                image_id=image_id,
            )
            
            result = await image_service.purge_image_by_id(action)
            
            assert isinstance(result, PurgeImageByIdActionResult)
            assert result.image.id == image_id
            
            # Verify image is hard deleted
            async with database_engine.begin_session() as session:
                deleted_image = await session.get(ImageRow, image_id)
                assert deleted_image is None
    
    async def test_purge_image_with_aliases(
        self,
        image_service: ImageService,
        create_test_image,
        create_test_alias,
        database_engine: ExtendedAsyncSAEngine,
    ) -> None:
        """Test purging image also removes its aliases."""
        async with create_test_image() as image:
            image_id = image.id
            async with create_test_alias(alias="alias1", target_image_id=image_id) as alias1:
                async with create_test_alias(alias="alias2", target_image_id=image_id) as alias2:
                    alias1_id = alias1.id
                    alias2_id = alias2.id
                    
                    action = PurgeImageByIdAction(
                        user_id=uuid.uuid4(),
                        client_role=UserRole.SUPERADMIN,
                        image_id=image_id,
                    )
                    
                    result = await image_service.purge_image_by_id(action)
                    
                    assert isinstance(result, PurgeImageByIdActionResult)
                    
                    # Verify image and aliases are deleted
                    async with database_engine.begin_session() as session:
                        assert await session.get(ImageRow, image_id) is None
                        assert await session.get(ImageAliasRow, alias1_id) is None
                        assert await session.get(ImageAliasRow, alias2_id) is None


class TestScanImage:
    """Test cases for scan_image functionality."""
    
    async def test_scan_existing_image(
        self,
        image_service: ImageService,
        create_test_image,
    ) -> None:
        """Test scanning an existing image."""
        async with create_test_image(name="tensorflow:latest") as image:
            action = ScanImageAction(
                canonical="tensorflow:latest",
                architecture="x86_64",
            )
            
            # Mock the repository scan method
            with patch.object(
                image_service._image_repository,
                'scan_image_by_identifier',
                return_value=MagicMock(
                    images=[ImageData(
                        id=image.id,
                        name="tensorflow:latest",
                        architecture="x86_64",
                        registry="docker.io",
                        size_bytes=2048 * 1024 * 1024,  # 2GB
                        is_active=True,
                        created_at=datetime.utcnow(),
                        owner_email="test@example.com",
                    )],
                    errors=[]
                )
            ):
                result = await image_service.scan_image(action)
                
                assert isinstance(result, ScanImageActionResult)
                assert result.image.name == "tensorflow:latest"
                assert result.image.size_bytes == 2048 * 1024 * 1024
                assert result.errors == []
    
    async def test_scan_multi_arch_image(
        self,
        image_service: ImageService,
        create_test_image,
    ) -> None:
        """Test scanning a specific architecture of multi-arch image."""
        async with create_test_image(name="alpine:latest", architecture="arm64") as image:
            action = ScanImageAction(
                canonical="alpine:latest",
                architecture="arm64",
            )
            
            # Mock the repository scan method
            with patch.object(
                image_service._image_repository,
                'scan_image_by_identifier',
                return_value=MagicMock(
                    images=[ImageData(
                        id=image.id,
                        name="alpine:latest",
                        architecture="arm64",
                        registry="docker.io",
                        size_bytes=5 * 1024 * 1024,  # 5MB
                        is_active=True,
                        created_at=datetime.utcnow(),
                        owner_email="test@example.com",
                    )],
                    errors=[]
                )
            ):
                result = await image_service.scan_image(action)
                
                assert isinstance(result, ScanImageActionResult)
                assert result.image.architecture == "arm64"


class TestModifyImage:
    """Test cases for modify_image functionality."""
    
    async def test_modify_image_name(
        self,
        image_service: ImageService,
        create_test_image,
    ) -> None:
        """Test modifying image name."""
        async with create_test_image(name="old-name:latest") as image:
            action = ModifyImageAction(
                target="old-name:latest",
                architecture="x86_64",
                modifier=ImageModifier(name="new-name:latest"),
            )
            
            # Mock the repository update method
            with patch.object(
                image_service._image_repository,
                'update_image_properties',
                return_value=ImageData(
                    id=image.id,
                    name="new-name:latest",
                    architecture="x86_64",
                    registry="docker.io",
                    size_bytes=image.size_bytes,
                    is_active=True,
                    created_at=image.created_at,
                    owner_email=image.owner_email,
                )
            ):
                result = await image_service.modify_image(action)
                
                assert isinstance(result, ModifyImageActionResult)
                assert result.image.name == "new-name:latest"
    
    async def test_modify_image_resource_limits(
        self,
        image_service: ImageService,
        create_test_image,
    ) -> None:
        """Test modifying image resource limits."""
        async with create_test_image() as image:
            resource_limits = {"cpu": "4", "memory": "8G", "gpu": "1"}
            action = ModifyImageAction(
                target=image.name,
                architecture="x86_64",
                modifier=ImageModifier(resource_limits=resource_limits),
            )
            
            # Mock the repository update method
            with patch.object(
                image_service._image_repository,
                'update_image_properties',
                return_value=ImageData(
                    id=image.id,
                    name=image.name,
                    architecture="x86_64",
                    registry="docker.io",
                    size_bytes=image.size_bytes,
                    is_active=True,
                    created_at=image.created_at,
                    owner_email=image.owner_email,
                    resource_limits=resource_limits,
                )
            ):
                result = await image_service.modify_image(action)
                
                assert isinstance(result, ModifyImageActionResult)
                assert result.image.resource_limits == resource_limits
    
    async def test_modify_non_existent_image(
        self,
        image_service: ImageService,
    ) -> None:
        """Test modifying non-existent image."""
        action = ModifyImageAction(
            target="non-existent:latest",
            architecture="x86_64",
            modifier=ImageModifier(name="new-name:latest"),
        )
        
        # Mock the repository to raise UnknownImageReference
        with patch.object(
            image_service._image_repository,
            'update_image_properties',
            side_effect=UnknownImageReference
        ):
            with pytest.raises(UnknownImageReference):
                await image_service.modify_image(action)


class TestClearImageCustomResourceLimit:
    """Test cases for clear_image_custom_resource_limit functionality."""
    
    async def test_clear_resource_limits(
        self,
        image_service: ImageService,
        create_test_image,
    ) -> None:
        """Test clearing custom resource limits."""
        async with create_test_image() as image:
            action = ClearImageCustomResourceLimitAction(
                image_canonical=image.name,
                architecture="x86_64",
            )
            
            # Mock the repository clear method
            with patch.object(
                image_service._image_repository,
                'clear_image_custom_resource_limit',
                return_value=ImageData(
                    id=image.id,
                    name=image.name,
                    architecture="x86_64",
                    registry="docker.io",
                    size_bytes=image.size_bytes,
                    is_active=True,
                    created_at=image.created_at,
                    owner_email=image.owner_email,
                    resource_limits=None,  # Cleared
                )
            ):
                result = await image_service.clear_image_custom_resource_limit(action)
                
                assert isinstance(result, ClearImageCustomResourceLimitActionResult)
                assert result.image_data.resource_limits is None
    
    async def test_clear_already_empty_limits(
        self,
        image_service: ImageService,
        create_test_image,
    ) -> None:
        """Test clearing limits that are already empty (idempotent)."""
        async with create_test_image() as image:
            action = ClearImageCustomResourceLimitAction(
                image_canonical=image.name,
                architecture="x86_64",
            )
            
            # Mock the repository clear method
            with patch.object(
                image_service._image_repository,
                'clear_image_custom_resource_limit',
                return_value=ImageData(
                    id=image.id,
                    name=image.name,
                    architecture="x86_64",
                    registry="docker.io",
                    size_bytes=image.size_bytes,
                    is_active=True,
                    created_at=image.created_at,
                    owner_email=image.owner_email,
                    resource_limits=None,
                )
            ):
                result = await image_service.clear_image_custom_resource_limit(action)
                
                assert isinstance(result, ClearImageCustomResourceLimitActionResult)
                assert result.image_data.resource_limits is None


class TestAliasImage:
    """Test cases for alias_image functionality."""
    
    async def test_create_new_alias(
        self,
        image_service: ImageService,
        create_test_image,
    ) -> None:
        """Test creating a new alias for an image."""
        async with create_test_image(name="tensorflow/tensorflow:2.10.0-gpu") as image:
            action = AliasImageAction(
                alias="my-tensorflow",
                image_canonical="tensorflow/tensorflow:2.10.0-gpu",
                architecture="x86_64",
            )
            
            # Mock the repository add alias method
            with patch.object(
                image_service._image_repository,
                'add_image_alias',
                return_value=(image.id, ImageAlias("my-tensorflow"))
            ):
                result = await image_service.alias_image(action)
                
                assert isinstance(result, AliasImageActionResult)
                assert result.image_id == image.id
                assert result.image_alias == ImageAlias("my-tensorflow")
    
    async def test_alias_non_existent_target(
        self,
        image_service: ImageService,
    ) -> None:
        """Test creating alias for non-existent target image."""
        action = AliasImageAction(
            alias="new-alias",
            image_canonical="non-existent:latest",
            architecture="x86_64",
        )
        
        # Mock the repository to raise UnknownImageReference
        with patch.object(
            image_service._image_repository,
            'add_image_alias',
            side_effect=UnknownImageReference
        ):
            with pytest.raises(ImageNotFound):
                await image_service.alias_image(action)


class TestDealiasImage:
    """Test cases for dealias_image functionality."""
    
    async def test_remove_alias(
        self,
        image_service: ImageService,
        create_test_image,
        create_test_alias,
    ) -> None:
        """Test removing an existing alias."""
        async with create_test_image() as image:
            async with create_test_alias(alias="my-tensorflow", target_image_id=image.id) as alias:
                action = DealiasImageAction(alias="my-tensorflow")
                
                # Mock the repository delete alias method
                with patch.object(
                    image_service._image_repository,
                    'delete_image_alias',
                    return_value=(image.id, ImageAlias("my-tensorflow"))
                ):
                    result = await image_service.dealias_image(action)
                    
                    assert isinstance(result, DealiasImageActionResult)
                    assert result.image_id == image.id
                    assert result.image_alias == ImageAlias("my-tensorflow")
    
    async def test_remove_non_existent_alias(
        self,
        image_service: ImageService,
    ) -> None:
        """Test removing non-existent alias."""
        action = DealiasImageAction(alias="non-existent-alias")
        
        # Mock the repository to raise exception
        with patch.object(
            image_service._image_repository,
            'delete_image_alias',
            side_effect=ImageNotFound
        ):
            with pytest.raises(ImageNotFound):
                await image_service.dealias_image(action)


class TestUntagImageFromRegistry:
    """Test cases for untag_image_from_registry functionality."""
    
    async def test_untag_image_superadmin(
        self,
        image_service: ImageService,
        create_test_image,
    ) -> None:
        """Test untagging image from registry as superadmin."""
        async with create_test_image() as image:
            action = UntagImageFromRegistryAction(
                user_id=uuid.uuid4(),
                client_role=UserRole.SUPERADMIN,
                image_id=image.id,
            )
            
            # Mock the repository untag method
            with patch.object(
                image_service._admin_image_repository,
                'untag_image_from_registry_force',
                return_value=ImageData(
                    id=image.id,
                    name=image.name,
                    architecture="x86_64",
                    registry="docker.io",
                    size_bytes=image.size_bytes,
                    is_active=True,
                    created_at=image.created_at,
                    owner_email=image.owner_email,
                )
            ):
                result = await image_service.untag_image_from_registry(action)
                
                assert isinstance(result, UntagImageFromRegistryActionResult)
                assert result.image.id == image.id
    
    async def test_untag_image_regular_user_owner(
        self,
        image_service: ImageService,
        create_test_image,
    ) -> None:
        """Test regular user can untag their own image."""
        user_id = uuid.uuid4()
        user_email = f"user-{user_id}@example.com"
        
        async with create_test_image(owner_email=user_email) as image:
            action = UntagImageFromRegistryAction(
                user_id=user_id,
                client_role=UserRole.USER,
                image_id=image.id,
            )
            
            # Mock the repository untag method
            with patch.object(
                image_service._image_repository,
                'untag_image_from_registry_validated',
                return_value=ImageData(
                    id=image.id,
                    name=image.name,
                    architecture="x86_64",
                    registry="docker.io",
                    size_bytes=image.size_bytes,
                    is_active=True,
                    created_at=image.created_at,
                    owner_email=user_email,
                )
            ):
                result = await image_service.untag_image_from_registry(action)
                
                assert isinstance(result, UntagImageFromRegistryActionResult)
                assert result.image.id == image.id


class TestPurgeImages:
    """Test cases for purge_images functionality."""
    
    async def test_purge_images_from_single_agent(
        self,
        image_service: ImageService,
        mock_agent_registry: AgentRegistry,
        create_test_image,
    ) -> None:
        """Test purging images from a single agent."""
        async with create_test_image(name="ubuntu:20.04") as image1:
            async with create_test_image(name="python:3.9") as image2:
                agent_id = "agent-1"
                action = PurgeImagesAction(
                    keys=[
                        PurgeImagesKeyData(
                            agent_id=agent_id,
                            images=[
                                ImageRefData(name="ubuntu:20.04", architecture="x86_64"),
                                ImageRefData(name="python:3.9", architecture="x86_64"),
                            ]
                        )
                    ],
                    force=True,
                    noprune=False,
                )
                
                # Mock agent registry purge response
                mock_agent_registry.purge_images.return_value = MagicMock(
                    responses=[
                        MagicMock(image="ubuntu:20.04", error=None),
                        MagicMock(image="python:3.9", error=None),
                    ]
                )
                
                # Mock repository resolve methods
                with patch.object(
                    image_service._image_repository,
                    'resolve_images_batch',
                    return_value=[
                        ImageData(
                            id=image1.id,
                            name="ubuntu:20.04",
                            architecture="x86_64",
                            registry="docker.io",
                            size_bytes=image1.size_bytes,
                            is_active=True,
                            created_at=image1.created_at,
                            owner_email=image1.owner_email,
                        ),
                        ImageData(
                            id=image2.id,
                            name="python:3.9",
                            architecture="x86_64",
                            registry="docker.io",
                            size_bytes=image2.size_bytes,
                            is_active=True,
                            created_at=image2.created_at,
                            owner_email=image2.owner_email,
                        ),
                    ]
                ):
                    result = await image_service.purge_images(action)
                    
                    assert isinstance(result, PurgeImagesActionResult)
                    assert len(result.purged_images) == 1
                    assert result.purged_images[0].agent_id == agent_id
                    assert len(result.purged_images[0].purged_images) == 2
                    assert result.errors == []
                    assert result.total_reserved_bytes == image1.size_bytes + image2.size_bytes
    
    async def test_purge_images_from_multiple_agents(
        self,
        image_service: ImageService,
        mock_agent_registry: AgentRegistry,
        create_test_image,
    ) -> None:
        """Test purging images from multiple agents."""
        async with create_test_image(name="tensorflow:latest") as image:
            action = PurgeImagesAction(
                keys=[
                    PurgeImagesKeyData(
                        agent_id="agent-1",
                        images=[ImageRefData(name="tensorflow:latest", architecture="x86_64")]
                    ),
                    PurgeImagesKeyData(
                        agent_id="agent-2",
                        images=[ImageRefData(name="tensorflow:latest", architecture="x86_64")]
                    ),
                ],
                force=True,
                noprune=False,
            )
            
            # Mock agent registry purge responses
            mock_agent_registry.purge_images.side_effect = [
                MagicMock(responses=[MagicMock(image="tensorflow:latest", error=None)]),
                MagicMock(responses=[MagicMock(image="tensorflow:latest", error=None)]),
            ]
            
            # Mock repository resolve method
            with patch.object(
                image_service._image_repository,
                'resolve_images_batch',
                return_value=[
                    ImageData(
                        id=image.id,
                        name="tensorflow:latest",
                        architecture="x86_64",
                        registry="docker.io",
                        size_bytes=image.size_bytes,
                        is_active=True,
                        created_at=image.created_at,
                        owner_email=image.owner_email,
                    )
                ]
            ):
                result = await image_service.purge_images(action)
                
                assert isinstance(result, PurgeImagesActionResult)
                assert len(result.purged_images) == 2
                assert result.purged_images[0].agent_id == "agent-1"
                assert result.purged_images[1].agent_id == "agent-2"
                assert result.errors == []
    
    async def test_purge_images_partial_failure(
        self,
        image_service: ImageService,
        mock_agent_registry: AgentRegistry,
        create_test_image,
    ) -> None:
        """Test purging images with some failures."""
        async with create_test_image(name="pytorch:latest") as image:
            action = PurgeImagesAction(
                keys=[
                    PurgeImagesKeyData(
                        agent_id="agent-1",
                        images=[ImageRefData(name="pytorch:latest", architecture="x86_64")]
                    ),
                    PurgeImagesKeyData(
                        agent_id="offline-agent",
                        images=[ImageRefData(name="pytorch:latest", architecture="x86_64")]
                    ),
                ],
                force=True,
                noprune=False,
            )
            
            # Mock agent registry purge responses - one success, one failure
            mock_agent_registry.purge_images.side_effect = [
                MagicMock(responses=[MagicMock(image="pytorch:latest", error=None)]),
                MagicMock(responses=[MagicMock(image="pytorch:latest", error="Agent offline")]),
            ]
            
            # Mock repository resolve method
            with patch.object(
                image_service._image_repository,
                'resolve_images_batch',
                return_value=[
                    ImageData(
                        id=image.id,
                        name="pytorch:latest",
                        architecture="x86_64",
                        registry="docker.io",
                        size_bytes=image.size_bytes,
                        is_active=True,
                        created_at=image.created_at,
                        owner_email=image.owner_email,
                    )
                ]
            ):
                result = await image_service.purge_images(action)
                
                assert isinstance(result, PurgeImagesActionResult)
                assert len(result.purged_images) == 2
                assert len(result.purged_images[0].purged_images) == 1  # Success
                assert len(result.purged_images[1].purged_images) == 0  # Failure
                assert len(result.errors) == 1
                assert "Agent offline" in result.errors[0]