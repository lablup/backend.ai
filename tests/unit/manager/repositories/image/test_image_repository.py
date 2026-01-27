"""
Tests for ImageRepository search functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from unittest.mock import MagicMock

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.image import ImageAliasRow, ImageRow, ImageStatus, ImageType
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.image.repository import ImageRepository
from ai.backend.testutils.db import with_tables


class TestImageRepositorySearch:
    """Test cases for ImageRepository search functionality"""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created."""
        async with with_tables(
            database_connection,
            [
                ContainerRegistryRow,
                ImageRow,
                ImageAliasRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_registry_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> uuid.UUID:
        """Create test container registry and return registry ID"""
        registry_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            registry = ContainerRegistryRow(
                id=registry_id,
                url="https://registry.example.com",
                registry_name="registry.example.com",
                type=ContainerRegistryType.DOCKER,
                project="test_project",
                is_global=True,
            )
            db_sess.add(registry)
            await db_sess.commit()

        return registry_id

    @pytest.fixture
    async def sample_images(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_registry_id: uuid.UUID,
    ) -> AsyncGenerator[list[uuid.UUID], None]:
        """Create sample images for testing"""
        images_data = [
            ("python:3.9", "x86_64", ImageType.COMPUTE),
            ("python:3.10", "x86_64", ImageType.COMPUTE),
            ("nginx:latest", "x86_64", ImageType.SERVICE),
            ("ubuntu:22.04", "arm64", ImageType.SYSTEM),
        ]

        image_rows: list[ImageRow] = []
        async with db_with_cleanup.begin_session() as db_sess:
            for name, arch, img_type in images_data:
                image = ImageRow(
                    name=f"registry.example.com/test_project/{name}",
                    image=name.split(":")[0],
                    tag=name.split(":")[1],
                    registry="registry.example.com",
                    registry_id=test_registry_id,
                    project="test_project",
                    architecture=arch,
                    config_digest=f"sha256:{uuid.uuid4().hex}",
                    size_bytes=1000000,
                    type=img_type,
                    status=ImageStatus.ALIVE,
                    accelerators=None,
                    labels={},
                    resources={},
                )
                db_sess.add(image)
                image_rows.append(image)
            await db_sess.flush()
            image_ids = [row.id for row in image_rows]
            await db_sess.commit()

        yield image_ids

    @pytest.fixture
    async def sample_images_for_pagination(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_registry_id: uuid.UUID,
    ) -> AsyncGenerator[list[uuid.UUID], None]:
        """Create 25 images for pagination testing"""
        image_rows: list[ImageRow] = []

        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(25):
                image = ImageRow(
                    name=f"registry.example.com/test_project/image_{i:02d}:latest",
                    image=f"image_{i:02d}",
                    tag="latest",
                    registry="registry.example.com",
                    registry_id=test_registry_id,
                    project="test_project",
                    architecture="x86_64",
                    config_digest=f"sha256:{uuid.uuid4().hex}",
                    size_bytes=1000000,
                    type=ImageType.COMPUTE,
                    status=ImageStatus.ALIVE,
                    accelerators=None,
                    labels={},
                    resources={},
                )
                db_sess.add(image)
                image_rows.append(image)
            await db_sess.flush()
            image_ids = [row.id for row in image_rows]
            await db_sess.commit()

        yield image_ids

    @pytest.fixture
    def image_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> ImageRepository:
        """Create ImageRepository instance with database"""
        # ImageRepository requires valkey_image and config_provider
        # For search tests, we only need the db_source which uses db
        mock_valkey = MagicMock()
        mock_config = MagicMock()
        return ImageRepository(
            db=db_with_cleanup,
            valkey_image=mock_valkey,
            config_provider=mock_config,
        )

    # =========================================================================
    # Tests - Search with pagination
    # =========================================================================

    async def test_search_images_first_page(
        self,
        image_repository: ImageRepository,
        sample_images_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test first page of search results"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        result = await image_repository.search_images(querier)

        assert len(result.items) == 10
        assert result.total_count == 25

    async def test_search_images_second_page(
        self,
        image_repository: ImageRepository,
        sample_images_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test second page of search results"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=10),
            conditions=[],
            orders=[],
        )

        result = await image_repository.search_images(querier)

        assert len(result.items) == 10
        assert result.total_count == 25

    async def test_search_images_last_page(
        self,
        image_repository: ImageRepository,
        sample_images_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test last page with partial results"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=20),
            conditions=[],
            orders=[],
        )

        result = await image_repository.search_images(querier)

        assert len(result.items) == 5
        assert result.total_count == 25

    # =========================================================================
    # Tests - Search with filtering
    # =========================================================================

    async def test_search_images_filter_by_architecture(
        self,
        image_repository: ImageRepository,
        sample_images: list[uuid.UUID],
    ) -> None:
        """Test filtering images by architecture"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                lambda: ImageRow.architecture == "arm64",
            ],
            orders=[],
        )

        result = await image_repository.search_images(querier)

        assert len(result.items) == 1
        assert result.items[0].architecture == "arm64"

    async def test_search_images_filter_by_type(
        self,
        image_repository: ImageRepository,
        sample_images: list[uuid.UUID],
    ) -> None:
        """Test filtering images by type"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                lambda: ImageRow.type == ImageType.COMPUTE,
            ],
            orders=[],
        )

        result = await image_repository.search_images(querier)

        assert len(result.items) == 2
        for item in result.items:
            assert item.type == ImageType.COMPUTE

    # =========================================================================
    # Tests - Search with ordering
    # =========================================================================

    async def test_search_images_order_by_name_ascending(
        self,
        image_repository: ImageRepository,
        sample_images: list[uuid.UUID],
    ) -> None:
        """Test ordering images by name ascending"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[ImageRow.name.asc()],
        )

        result = await image_repository.search_images(querier)

        names = [str(item.name) for item in result.items]
        assert names == sorted(names)

    async def test_search_images_order_by_name_descending(
        self,
        image_repository: ImageRepository,
        sample_images: list[uuid.UUID],
    ) -> None:
        """Test ordering images by name descending"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[ImageRow.name.desc()],
        )

        result = await image_repository.search_images(querier)

        names = [str(item.name) for item in result.items]
        assert names == sorted(names, reverse=True)

    # =========================================================================
    # Tests - Empty results
    # =========================================================================

    async def test_search_images_no_results(
        self,
        image_repository: ImageRepository,
        sample_images: list[uuid.UUID],
    ) -> None:
        """Test search with no matching results"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                lambda: ImageRow.architecture == "nonexistent",
            ],
            orders=[],
        )

        result = await image_repository.search_images(querier)

        assert len(result.items) == 0
        assert result.total_count == 0
