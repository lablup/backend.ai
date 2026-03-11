"""Component tests for image search/query with filters, name patterns, and pagination."""

from __future__ import annotations

import uuid

import pytest

from ai.backend.client.v2.exceptions import NotFoundError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.image.request import (
    ImageFilter,
    ImageOrder,
    SearchImagesRequest,
)
from ai.backend.common.dto.manager.image.response import GetImageResponse, SearchImagesResponse
from ai.backend.common.dto.manager.image.types import ImageOrderField, OrderDirection
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.manager.data.image.types import ImageStatus

from .conftest import ImageFactoryHelper


class TestImageSearchNoFilter:
    """Search with no filter returns ALIVE images."""

    async def test_no_filter_returns_alive_images(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """S-1: Search with no filter returns at least the pre-seeded ALIVE image."""
        image_id, _ = image_fixture
        result = await admin_registry.image.search(SearchImagesRequest())
        assert isinstance(result, SearchImagesResponse)
        assert result.pagination.total >= 1
        found_ids = [item.id for item in result.items]
        assert image_id in found_ids

    async def test_deleted_image_still_appears_in_unfiltered_search(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """S-2: DELETED image appears in unfiltered search (no default status filter)."""
        _, helper = image_fixture
        deleted_id = await helper.create(
            name_suffix="deleted-img",
            status=ImageStatus.DELETED,
        )
        result = await admin_registry.image.search(SearchImagesRequest())
        found_ids = [item.id for item in result.items]
        assert deleted_id in found_ids


class TestImageSearchByArchitecture:
    """Filter by architecture returns matching images only."""

    async def test_filter_architecture_equals(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """S-3: Filter architecture equals 'aarch64' returns only aarch64 images."""
        x86_id, helper = image_fixture  # default x86_64
        arm_id = await helper.create(name_suffix="arm-image", architecture="aarch64")

        result = await admin_registry.image.search(
            SearchImagesRequest(
                filter=ImageFilter(
                    architecture=StringFilter(equals="aarch64"),
                ),
            )
        )
        assert isinstance(result, SearchImagesResponse)
        found_ids = [item.id for item in result.items]
        assert arm_id in found_ids
        assert x86_id not in found_ids
        for item in result.items:
            assert item.architecture == "aarch64"

    async def test_filter_architecture_contains(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """S-4: Filter architecture contains 'x86' returns x86_64 images."""
        image_id, helper = image_fixture  # x86_64
        await helper.create(name_suffix="arm-only", architecture="aarch64")

        result = await admin_registry.image.search(
            SearchImagesRequest(
                filter=ImageFilter(
                    architecture=StringFilter(contains="x86"),
                ),
            )
        )
        found_ids = [item.id for item in result.items]
        assert image_id in found_ids
        for item in result.items:
            assert "x86" in item.architecture


class TestImageSearchByName:
    """Filter by name with different string match patterns."""

    async def test_filter_name_contains(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """S-5: Filter name contains returns matching images."""
        _, helper = image_fixture
        target_id = await helper.create(name_suffix="unique-needle-name")

        result = await admin_registry.image.search(
            SearchImagesRequest(
                filter=ImageFilter(
                    name=StringFilter(contains="unique-needle-name"),
                ),
            )
        )
        assert isinstance(result, SearchImagesResponse)
        found_ids = [item.id for item in result.items]
        assert target_id in found_ids
        assert result.pagination.total >= 1

    async def test_filter_name_equals(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """S-6: Filter name equals returns only the exact-match image."""
        _, helper = image_fixture
        suffix = f"exact-{uuid.uuid4().hex[:8]}"
        target_id = await helper.create(name_suffix=suffix)
        canonical = f"registry.test.local/testproject/test-image-{suffix}:latest"

        result = await admin_registry.image.search(
            SearchImagesRequest(
                filter=ImageFilter(
                    name=StringFilter(equals=canonical),
                ),
            )
        )
        assert isinstance(result, SearchImagesResponse)
        assert result.pagination.total == 1
        assert result.items[0].id == target_id

    async def test_filter_name_starts_with(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """S-7: Filter name starts_with matches images with that prefix."""
        image_id, _ = image_fixture
        result = await admin_registry.image.search(
            SearchImagesRequest(
                filter=ImageFilter(
                    name=StringFilter(starts_with="registry.test.local/testproject/"),
                ),
            )
        )
        assert isinstance(result, SearchImagesResponse)
        found_ids = [item.id for item in result.items]
        assert image_id in found_ids
        for item in result.items:
            assert item.name.startswith("registry.test.local/testproject/")

    async def test_filter_name_no_match_returns_empty(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """S-8: Filter name with non-existent value returns empty list."""
        result = await admin_registry.image.search(
            SearchImagesRequest(
                filter=ImageFilter(
                    name=StringFilter(contains="absolutely-no-such-image-exists"),
                ),
            )
        )
        assert isinstance(result, SearchImagesResponse)
        assert result.pagination.total == 0
        assert len(result.items) == 0


class TestImageSearchPagination:
    """Pagination with limit and offset."""

    async def test_limit_restricts_result_count(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """S-9: limit=1 returns at most 1 result with correct total."""
        _, helper = image_fixture
        await helper.create(name_suffix="pagination-extra")

        result = await admin_registry.image.search(
            SearchImagesRequest(limit=1),
        )
        assert isinstance(result, SearchImagesResponse)
        assert len(result.items) <= 1
        assert result.pagination.total >= 2

    async def test_offset_skips_items(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """S-10: offset skips the specified number of items."""
        _, helper = image_fixture
        await helper.create(name_suffix="offset-extra")

        all_result = await admin_registry.image.search(SearchImagesRequest())
        total = all_result.pagination.total
        assert total >= 2

        offset_result = await admin_registry.image.search(
            SearchImagesRequest(offset=1),
        )
        assert offset_result.pagination.total == total
        assert len(offset_result.items) == total - 1

    async def test_ordering_by_name_ascending(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """S-11: Order by name ASC returns images sorted alphabetically."""
        _, helper = image_fixture
        await helper.create(name_suffix="zzz-last")
        await helper.create(name_suffix="aaa-first")

        result = await admin_registry.image.search(
            SearchImagesRequest(
                order=[ImageOrder(field=ImageOrderField.NAME, direction=OrderDirection.ASC)],
            ),
        )
        assert isinstance(result, SearchImagesResponse)
        names = [item.name for item in result.items]
        assert names == sorted(names)


class TestImageGet:
    """Get image detail by ID."""

    async def test_get_by_id_returns_full_image_data(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """S-12: Get by ID returns complete ImageDTO with expected fields."""
        image_id, _ = image_fixture
        result = await admin_registry.image.get(image_id)
        assert isinstance(result, GetImageResponse)
        assert result.item.id == image_id
        assert result.item.architecture == "x86_64"
        assert result.item.status == "ALIVE"
        assert result.item.registry == "registry.test.local"
        assert result.item.project == "testproject"
        assert result.item.tag == "latest"
        assert result.item.size_bytes == 1024000
        assert result.item.type == "COMPUTE"
        assert result.item.is_local is False
        assert result.item.name.startswith("registry.test.local/testproject/test-image-")

    async def test_get_nonexistent_id_returns_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """S-13: Get with random UUID raises NotFoundError (404)."""
        with pytest.raises(NotFoundError):
            await admin_registry.image.get(uuid.uuid4())
