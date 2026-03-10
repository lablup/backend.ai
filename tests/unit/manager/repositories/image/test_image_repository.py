"""
Tests for ImageRepository search functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Callable, Coroutine
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.common.types import BinarySize, ImageID, KernelId, ResourceSlot, SessionId
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.image import ImageAliasRow, ImageRow, ImageStatus, ImageType
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.image.options import ImageConditions
from ai.backend.manager.repositories.image.repository import ImageRepository
from ai.backend.testutils.db import with_tables

CreateKernelForImageFunc = Callable[[ImageRow, datetime], Coroutine[Any, Any, None]]


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
    ) -> UUID:
        """Create test container registry and return registry ID"""
        registry_id = uuid4()

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
        test_registry_id: UUID,
    ) -> AsyncGenerator[list[UUID], None]:
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
                    config_digest=f"sha256:{uuid4().hex}",
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
        test_registry_id: UUID,
    ) -> AsyncGenerator[list[UUID], None]:
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
                    config_digest=f"sha256:{uuid4().hex}",
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
        sample_images_for_pagination: list[UUID],
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
        sample_images_for_pagination: list[UUID],
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
        sample_images_for_pagination: list[UUID],
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
        sample_images: list[UUID],
    ) -> None:
        """Test filtering images by architecture"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            # TODO: Refactor after adding Condition type
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
        sample_images: list[UUID],
    ) -> None:
        """Test filtering images by type"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            # TODO: Refactor after adding Condition type
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
        sample_images: list[UUID],
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
        sample_images: list[UUID],
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
        sample_images: list[UUID],
    ) -> None:
        """Test search with no matching results"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            # TODO: Refactor after adding Condition type
            conditions=[
                lambda: ImageRow.architecture == "nonexistent",
            ],
            orders=[],
        )

        result = await image_repository.search_images(querier)

        assert len(result.items) == 0
        assert result.total_count == 0

    # =========================================================================
    # Tests - Alias filter conditions
    # =========================================================================

    @pytest.fixture
    async def images_with_aliases(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_registry_id: UUID,
    ) -> AsyncGenerator[list[UUID], None]:
        """Create images with aliases for alias filter testing."""
        images_data = [
            ("python:3.9", "x86_64", ImageType.COMPUTE, ["py39"]),
            ("nginx:latest", "x86_64", ImageType.SERVICE, ["webserver"]),
            ("ubuntu:22.04", "arm64", ImageType.SYSTEM, []),
        ]

        image_rows: list[ImageRow] = []
        async with db_with_cleanup.begin_session() as db_sess:
            for name, arch, img_type, aliases in images_data:
                image = ImageRow(
                    name=f"registry.example.com/test_project/{name}",
                    image=name.split(":")[0],
                    tag=name.split(":")[1],
                    registry="registry.example.com",
                    registry_id=test_registry_id,
                    project="test_project",
                    architecture=arch,
                    config_digest=f"sha256:{uuid4().hex}",
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

            for image_row, (_, _, _, aliases) in zip(image_rows, images_data, strict=False):
                for alias_name in aliases:
                    alias = ImageAliasRow(
                        alias=alias_name,
                        image_id=image_row.id,
                    )
                    db_sess.add(alias)

            image_ids = [row.id for row in image_rows]
            await db_sess.commit()

        yield image_ids

    async def test_filter_by_single_alias_condition(
        self,
        image_repository: ImageRepository,
        images_with_aliases: list[UUID],
    ) -> None:
        """Test filtering images with a single alias condition."""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                ImageConditions.by_alias_contains(
                    StringMatchSpec(value="py", case_insensitive=False, negated=False)
                ),
            ],
            orders=[],
        )
        result = await image_repository.search_images(querier)
        assert result.total_count == 1
        assert "python" in str(result.items[0].name)

    async def test_filter_by_combined_alias_conditions(
        self,
        image_repository: ImageRepository,
        images_with_aliases: list[UUID],
    ) -> None:
        """Test filtering images with two alias conditions combined."""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                ImageConditions.by_alias_contains(
                    StringMatchSpec(value="py", case_insensitive=False, negated=False)
                ),
                ImageConditions.by_alias_ends_with(
                    StringMatchSpec(value="39", case_insensitive=False, negated=False)
                ),
            ],
            orders=[],
        )
        result = await image_repository.search_images(querier)
        assert result.total_count == 1
        assert "python:3.9" in str(result.items[0].name)


class TestImageRepositoryLoadLastUsed:
    """Test cases for ImageRepository.load_image_last_used()"""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with all tables needed for kernel queries."""
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents before children
                DomainRow,
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                AgentRow,
                ContainerRegistryRow,
                ImageRow,
                SessionRow,
                KernelRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def image_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> ImageRepository:
        mock_valkey = MagicMock()
        mock_config = MagicMock()
        return ImageRepository(
            db=db_with_cleanup,
            valkey_image=mock_valkey,
            config_provider=mock_config,
        )

    @pytest.fixture
    async def domain(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DomainRow:
        domain = DomainRow(name=f"test-{uuid4()}")
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(domain)
            await db_sess.flush()
        return domain

    @pytest.fixture
    async def user_policy(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> UserResourcePolicyRow:
        policy = UserResourcePolicyRow(
            name=f"{uuid4()}",
            max_vfolder_count=10,
            max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
            max_session_count_per_model_session=5,
            max_customized_image_count=3,
        )
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(policy)
            await db_sess.flush()
        return policy

    @pytest.fixture
    async def group_policy(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> ProjectResourcePolicyRow:
        policy = ProjectResourcePolicyRow(
            name=f"{uuid4()}",
            max_vfolder_count=10,
            max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
            max_network_count=5,
        )
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(policy)
            await db_sess.flush()
        return policy

    @pytest.fixture
    async def user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain: DomainRow,
        user_policy: UserResourcePolicyRow,
    ) -> UserRow:
        user = UserRow(
            uuid=uuid4(),
            email=f"test-{uuid4().hex[:8]}@example.com",
            domain_name=domain.name,
            resource_policy=user_policy.name,
        )
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(user)
            await db_sess.flush()
        return user

    @pytest.fixture
    async def group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain: DomainRow,
        group_policy: ProjectResourcePolicyRow,
    ) -> GroupRow:
        group = GroupRow(
            id=uuid4(),
            name=f"test-group-{uuid4().hex[:8]}",
            domain_name=domain.name,
            resource_policy=group_policy.name,
        )
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(group)
            await db_sess.flush()
        return group

    @pytest.fixture
    async def test_registry_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> UUID:
        registry_id = uuid4()
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
            await db_sess.flush()
        return registry_id

    @pytest.fixture
    async def sample_images(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_registry_id: UUID,
    ) -> list[ImageRow]:
        """Create sample images and return their rows."""
        images_data = [
            ("python:3.9", "x86_64"),
            ("python:3.10", "x86_64"),
            ("nginx:latest", "x86_64"),
        ]
        image_rows: list[ImageRow] = []
        async with db_with_cleanup.begin_session() as db_sess:
            for name, arch in images_data:
                image = ImageRow(
                    name=f"registry.example.com/test_project/{name}",
                    image=name.split(":")[0],
                    tag=name.split(":")[1],
                    registry="registry.example.com",
                    registry_id=test_registry_id,
                    project="test_project",
                    architecture=arch,
                    config_digest=f"sha256:{uuid4().hex}",
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
            await db_sess.commit()
        return image_rows

    @pytest.fixture
    def create_kernel_for_image(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        user: UserRow,
        group: GroupRow,
        domain: DomainRow,
    ) -> CreateKernelForImageFunc:
        """Return a factory that creates a session + kernel for the given image."""

        async def _create(image: ImageRow, created_at: datetime) -> None:
            session_id = SessionId(uuid4())
            async with db_with_cleanup.begin_session() as db_sess:
                session = SessionRow(
                    id=session_id,
                    name=f"sess-{uuid4()}",
                    user_uuid=user.uuid,
                    group_id=group.id,
                    domain_name=domain.name,
                    occupying_slots=ResourceSlot(),
                    requested_slots=ResourceSlot(),
                    vfolder_mounts=[],
                )
                db_sess.add(session)
                await db_sess.flush()

                kernel = KernelRow(
                    id=KernelId(uuid4()),
                    session_id=session_id,
                    image=image.name,
                    architecture=image.architecture,
                    domain_name=domain.name,
                    group_id=group.id,
                    user_uuid=user.uuid,
                    occupied_slots=ResourceSlot(),
                    requested_slots=ResourceSlot(),
                    repl_in_port=0,
                    repl_out_port=0,
                    stdin_port=0,
                    stdout_port=0,
                    created_at=created_at,
                )
                db_sess.add(kernel)
                await db_sess.flush()
                await db_sess.commit()

        return _create

    async def test_load_image_last_used_returns_most_recent(
        self,
        image_repository: ImageRepository,
        sample_images: list[ImageRow],
        create_kernel_for_image: CreateKernelForImageFunc,
    ) -> None:
        """Test that load_image_last_used returns the most recent kernel created_at."""
        now = datetime.now(UTC)
        older = now - timedelta(hours=2)
        newer = now - timedelta(hours=1)
        img = sample_images[0]

        await create_kernel_for_image(img, older)
        await create_kernel_for_image(img, newer)

        result = await image_repository.load_image_last_used([ImageID(img.id)])

        assert ImageID(img.id) in result
        assert abs(result[ImageID(img.id)].timestamp() - newer.timestamp()) < 1.0

    async def test_load_image_last_used_excludes_unused_images(
        self,
        image_repository: ImageRepository,
        sample_images: list[ImageRow],
        create_kernel_for_image: CreateKernelForImageFunc,
    ) -> None:
        """Test that only used images appear in the result; unused ones are excluded."""
        now = datetime.now(UTC)

        await create_kernel_for_image(sample_images[0], now - timedelta(hours=3))
        await create_kernel_for_image(sample_images[1], now - timedelta(hours=1))

        image_ids = [ImageID(img.id) for img in sample_images]
        result = await image_repository.load_image_last_used(image_ids)

        assert len(result) == 2
        assert ImageID(sample_images[0].id) in result
        assert ImageID(sample_images[1].id) in result
        assert ImageID(sample_images[2].id) not in result
