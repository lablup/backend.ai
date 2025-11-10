"""
Tests for ContainerRegistryRepository and AdminContainerRegistryRepository functionality.
Integration tests using real database operations.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from uuid import UUID

import pytest
import sqlalchemy as sa

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.data.image.types import ImageStatus, ImageType
from ai.backend.manager.errors.image import ContainerRegistryNotFound
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.container_registry.admin_repository import (
    AdminContainerRegistryRepository,
)
from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)


class TestContainerRegistryRepository:
    """Integration tests for ContainerRegistryRepository using real database"""

    @pytest.fixture
    def repository(self, database_engine: ExtendedAsyncSAEngine) -> ContainerRegistryRepository:
        """Create ContainerRegistryRepository instance with real database"""
        return ContainerRegistryRepository(db=database_engine)

    @pytest.fixture
    def admin_repository(
        self, database_engine: ExtendedAsyncSAEngine
    ) -> AdminContainerRegistryRepository:
        """Create AdminContainerRegistryRepository instance with real database"""
        return AdminContainerRegistryRepository(db=database_engine)

    @asynccontextmanager
    async def create_test_registry(
        self,
        database_engine: ExtendedAsyncSAEngine,
        registry_name: str = "test-registry.example.com",
        project: str | None = "test-project",
    ) -> AsyncGenerator[ContainerRegistryData, None]:
        """Create a test container registry and ensure cleanup"""
        async with database_engine.begin_session() as session:
            registry = ContainerRegistryRow(
                url=f"https://{registry_name}",
                registry_name=registry_name,
                type=ContainerRegistryType.HARBOR2,
                project=project,
                username=None,
                password=None,
                ssl_verify=True,
                is_global=True,
                extra=None,
            )
            session.add(registry)
            await session.flush()

            registry_data = registry.to_dataclass()

        try:
            yield registry_data
        finally:
            async with database_engine.begin_session() as session:
                await session.execute(
                    sa.delete(ImageRow).where(
                        (ImageRow.registry == registry_name)
                        & (ImageRow.project == project if project else sa.true())
                    )
                )
                await session.execute(
                    sa.delete(ContainerRegistryRow).where(
                        (ContainerRegistryRow.registry_name == registry_name)
                        & (ContainerRegistryRow.project == project if project else sa.true())
                    )
                )

    @asynccontextmanager
    async def create_test_images_for_registry(
        self,
        database_engine: ExtendedAsyncSAEngine,
        registry_data: ContainerRegistryData,
        image_names: list[str],
    ) -> AsyncGenerator[list[UUID], None]:
        """Create multiple test images for a registry and return their IDs"""
        image_ids = []
        for image_name in image_names:
            image_id = await self.create_test_image(
                database_engine,
                registry_data.id,
                registry_data.registry_name,
                registry_data.project,
                image_name,
                ImageStatus.ALIVE,
            )
            image_ids.append(image_id)

        try:
            yield image_ids
        finally:
            # Cleanup is handled by create_test_registry
            pass

    async def create_test_image(
        self,
        database_engine: ExtendedAsyncSAEngine,
        registry_id: UUID,
        registry_name: str,
        project: Optional[str] = "library",
        image_name: str = "test-image",
        status: ImageStatus = ImageStatus.ALIVE,
    ) -> UUID:
        """Create a test image for the registry"""
        async with database_engine.begin_session() as session:
            image = ImageRow(
                name=f"{registry_name}/{project or 'library'}/{image_name}:latest",
                registry=registry_name,
                registry_id=registry_id,
                project=project,
                image=image_name,
                tag="latest",
                architecture="x86_64",
                is_local=False,
                type=ImageType.COMPUTE,
                config_digest="sha256:test",
                size_bytes=1024 * 1024,  # 1MB
                accelerators=None,
                resources={},
                labels={},
                status=status,
            )
            session.add(image)
            await session.flush()

        return image.id

    @pytest.mark.asyncio
    async def test_get_by_registry_and_project_success(
        self, repository: ContainerRegistryRepository, database_engine: ExtendedAsyncSAEngine
    ) -> None:
        """Test successful registry retrieval by name and project"""
        project_name = "test-project"
        registry_name = "test-registry.example.com"
        async with self.create_test_registry(
            database_engine, registry_name, project_name
        ) as registry_data:
            # When
            result = await repository.get_by_registry_and_project(registry_name, project_name)

            # Then
            assert result is not None
            assert isinstance(result, ContainerRegistryData)
            assert result.registry_name == registry_name
            assert result.project == project_name
            assert result.id == registry_data.id

    @pytest.mark.asyncio
    async def test_get_by_registry_and_project_not_found(
        self, repository: ContainerRegistryRepository
    ) -> None:
        """Test registry retrieval when registry doesn't exist"""
        with pytest.raises(ContainerRegistryNotFound):
            await repository.get_by_registry_and_project("non-existent", "project")

    @pytest.mark.asyncio
    async def test_get_by_registry_name(
        self, repository: ContainerRegistryRepository, database_engine: ExtendedAsyncSAEngine
    ) -> None:
        """Test retrieving all registries with the same name"""
        registry_name = "test-registry.example.com"
        project1_name = "project1"
        project2_name = "project2"

        async with (
            self.create_test_registry(database_engine, registry_name, project1_name),
            self.create_test_registry(database_engine, registry_name, project2_name),
        ):
            # When
            results = await repository.get_by_registry_name(registry_name)

            # Then
            assert len(results) >= 2
            for result in results:
                assert result.registry_name == registry_name

    @pytest.mark.asyncio
    async def test_get_all(
        self, repository: ContainerRegistryRepository, database_engine: ExtendedAsyncSAEngine
    ) -> None:
        """Test retrieving all registries"""
        registry1_name = "test-registry1.example.com"
        registry2_name = "test-registry2.example.com"
        project1_name = "project1"
        project2_name = "project2"

        async with (
            self.create_test_registry(database_engine, registry1_name, project1_name),
            self.create_test_registry(database_engine, registry2_name, project2_name),
        ):
            # When
            result = await repository.get_all()

            # Then
            assert len(result) >= 2

    @pytest.mark.asyncio
    async def test_clear_images(
        self, repository: ContainerRegistryRepository, database_engine: ExtendedAsyncSAEngine
    ) -> None:
        """Test clearing images for a registry"""
        registry_name = "test-registry.example.com"
        project_name = "test-project"

        async with self.create_test_registry(
            database_engine, registry_name, project_name
        ) as registry_data:
            # Create test images
            image_id1 = await self.create_test_image(
                database_engine,
                registry_data.id,
                registry_name,
                project_name,
                "image1",
            )
            image_id2 = await self.create_test_image(
                database_engine,
                registry_data.id,
                registry_name,
                project_name,
                "image2",
            )

            # When
            result = await repository.clear_images(registry_name, project_name)

            # Then
            assert result is not None
            assert result.registry_name == registry_name

            # Verify images are marked as deleted
            async with database_engine.begin_readonly_session() as session:
                images = (
                    (
                        await session.execute(
                            sa.select(ImageRow).where(ImageRow.id.in_([image_id1, image_id2]))
                        )
                    )
                    .scalars()
                    .all()
                )
                assert all(img.status == ImageStatus.DELETED for img in images)

    @pytest.mark.asyncio
    async def test_clear_images_not_found(self, repository: ContainerRegistryRepository) -> None:
        """Test clearing images when registry not found"""
        with pytest.raises(ContainerRegistryNotFound):
            await repository.clear_images("non-existent", "project")

    @pytest.mark.asyncio
    async def test_clear_images_with_project_filter(
        self, repository: ContainerRegistryRepository, database_engine: ExtendedAsyncSAEngine
    ) -> None:
        """Test clearing images with project filter doesn't affect other projects"""
        registry_name = "test-registry.example.com"
        project1_name = "project1"
        project2_name = "project2"

        async with (
            self.create_test_registry(
                database_engine, registry_name, project1_name
            ) as registry_data1,
            self.create_test_registry(
                database_engine, registry_name, project2_name
            ) as registry_data2,
        ):
            # Create images in different projects
            image_id_in_project1 = await self.create_test_image(
                database_engine,
                registry_data1.id,
                registry_name,
                project1_name,
                "image1",
            )
            image_id_in_project2 = await self.create_test_image(
                database_engine,
                registry_data2.id,
                registry_name,
                project2_name,
                "image2",
            )

            # When - Clear images only for project1
            await repository.clear_images(registry_name, project1_name)

            # Then - Verify only project1 images are deleted
            async with database_engine.begin_readonly_session() as session:
                img_p1 = await session.scalar(
                    sa.select(ImageRow).where(ImageRow.id == image_id_in_project1)
                )
                img_p2 = await session.scalar(
                    sa.select(ImageRow).where(ImageRow.id == image_id_in_project2)
                )

                assert img_p1.status == ImageStatus.DELETED
                assert img_p2.status == ImageStatus.ALIVE

    @pytest.mark.asyncio
    async def test_get_registry_row_for_scanner_success(
        self, repository: ContainerRegistryRepository, database_engine: ExtendedAsyncSAEngine
    ) -> None:
        """Test getting registry row for scanner"""
        registry_name = "test-registry.example.com"
        project_name = "test-project"

        async with self.create_test_registry(
            database_engine, registry_name, project_name
        ) as registry_data:
            # When
            result = await repository.get_registry_row_for_scanner(registry_name, project_name)

            # Then
            assert result is not None
            assert isinstance(result, ContainerRegistryRow)
            assert result.registry_name == registry_name
            assert result.project == project_name
            assert result.id == registry_data.id

    @pytest.mark.asyncio
    async def test_get_registry_row_for_scanner_not_found(
        self, repository: ContainerRegistryRepository
    ) -> None:
        """Test getting registry row when not found"""
        with pytest.raises(ContainerRegistryNotFound):
            await repository.get_registry_row_for_scanner("non-existent", "project")
