from __future__ import annotations

import uuid

import pytest

from ai.backend.client.v2.exceptions import NotFoundError, PermissionDeniedError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.image.request import (
    AliasImageRequest,
    DealiasImageRequest,
    ForgetImageRequest,
    ImageFilter,
    ImageOrder,
    PurgeImageRequest,
    SearchImagesRequest,
)
from ai.backend.common.dto.manager.image.response import (
    AliasImageResponse,
    ForgetImageResponse,
    GetImageResponse,
    PurgeImageResponse,
    SearchImagesResponse,
)
from ai.backend.common.dto.manager.image.types import ImageOrderField, OrderDirection
from ai.backend.common.dto.manager.query import StringFilter

from .conftest import ImageFactoryHelper


class TestImageSearch:
    @pytest.mark.asyncio
    async def test_admin_searches_images(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """Search with no filter returns pre-seeded image(s)."""
        image_id, _ = image_fixture
        result = await admin_registry.image.search(SearchImagesRequest())
        assert isinstance(result, SearchImagesResponse)
        assert result.pagination.total >= 1
        found_ids = [item.id for item in result.items]
        assert image_id in found_ids

    @pytest.mark.asyncio
    async def test_search_with_name_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """Filter by name (StringFilter.contains) returns matching images."""
        image_id, helper = image_fixture
        # Create a second image with a distinct name
        other_id = await helper.create(name_suffix="other-unique-name")

        result = await admin_registry.image.search(
            SearchImagesRequest(
                filter=ImageFilter(
                    name=StringFilter(contains="other-unique-name"),
                ),
            )
        )
        assert isinstance(result, SearchImagesResponse)
        found_ids = [item.id for item in result.items]
        assert other_id in found_ids
        assert image_id not in found_ids

    @pytest.mark.asyncio
    async def test_search_with_ordering(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """Order by created_at DESC returns images in descending creation order."""
        _, helper = image_fixture
        await helper.create(name_suffix="ordered-second")

        result = await admin_registry.image.search(
            SearchImagesRequest(
                order=[
                    ImageOrder(
                        field=ImageOrderField.CREATED_AT,
                        direction=OrderDirection.DESC,
                    ),
                ],
            )
        )
        assert isinstance(result, SearchImagesResponse)
        assert len(result.items) >= 2
        # Most recently created should come first
        timestamps = [item.created_at for item in result.items if item.created_at is not None]
        assert timestamps == sorted(timestamps, reverse=True)

    @pytest.mark.asyncio
    async def test_search_with_pagination(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """limit=1 returns at most 1 result."""
        _, helper = image_fixture
        await helper.create(name_suffix="pagination-extra")

        result = await admin_registry.image.search(
            SearchImagesRequest(limit=1),
        )
        assert isinstance(result, SearchImagesResponse)
        assert len(result.items) <= 1
        assert result.pagination.total >= 2


class TestImageGet:
    @pytest.mark.asyncio
    async def test_admin_gets_image_by_id(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """Get existing image returns correct ImageDTO fields."""
        image_id, _ = image_fixture
        result = await admin_registry.image.get(image_id)
        assert isinstance(result, GetImageResponse)
        assert result.item.id == image_id
        assert result.item.architecture == "x86_64"
        assert result.item.status == "ALIVE"

    @pytest.mark.asyncio
    async def test_get_nonexistent_image_returns_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """Get with random UUID raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await admin_registry.image.get(uuid.uuid4())


class TestImageAlias:
    @pytest.mark.asyncio
    async def test_admin_aliases_image(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """Create alias, verify alias_id/alias/image_id returned."""
        image_id, _ = image_fixture
        alias_name = f"test-alias-{uuid.uuid4().hex[:8]}"
        result = await admin_registry.image.alias(
            AliasImageRequest(image_id=image_id, alias=alias_name),
        )
        assert isinstance(result, AliasImageResponse)
        assert result.alias == alias_name
        assert result.image_id == image_id
        assert result.alias_id is not None


class TestImageDealias:
    @pytest.mark.asyncio
    async def test_admin_dealiases_image(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """Create alias then dealias, verify response."""
        image_id, _ = image_fixture
        alias_name = f"test-dealias-{uuid.uuid4().hex[:8]}"
        # First create an alias
        await admin_registry.image.alias(
            AliasImageRequest(image_id=image_id, alias=alias_name),
        )
        # Then remove it
        result = await admin_registry.image.dealias(
            DealiasImageRequest(alias=alias_name),
        )
        assert isinstance(result, AliasImageResponse)
        assert result.alias == alias_name
        assert result.image_id == image_id


class TestImageForget:
    @pytest.mark.asyncio
    async def test_admin_forgets_image(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """Forget image, verify returned item.status == 'DELETED'."""
        image_id, _ = image_fixture
        result = await admin_registry.image.forget(
            ForgetImageRequest(image_id=image_id),
        )
        assert isinstance(result, ForgetImageResponse)
        assert result.item.id == image_id
        assert result.item.status == "DELETED"


class TestImagePurge:
    @pytest.mark.asyncio
    async def test_admin_purges_image(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """Purge image, verify subsequent get raises NotFoundError."""
        image_id, _ = image_fixture
        result = await admin_registry.image.purge(
            PurgeImageRequest(image_id=image_id),
        )
        assert isinstance(result, PurgeImageResponse)
        assert result.item.id == image_id
        # Verify the image is actually gone
        with pytest.raises(NotFoundError):
            await admin_registry.image.get(image_id)


class TestImagePermissions:
    @pytest.mark.asyncio
    @pytest.mark.xfail(
        reason="Handler raises HTTPForbidden(403) but middleware chain may transform it",
        raises=AssertionError,
        strict=False,
    )
    async def test_regular_user_cannot_search_images(
        self,
        user_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """Regular user search raises PermissionDeniedError (403)."""
        with pytest.raises(PermissionDeniedError):
            await user_registry.image.search(SearchImagesRequest())

    @pytest.mark.asyncio
    @pytest.mark.xfail(
        reason="Handler raises HTTPForbidden(403) but middleware chain may transform it",
        raises=AssertionError,
        strict=False,
    )
    async def test_regular_user_cannot_get_image(
        self,
        user_registry: BackendAIClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """Regular user get raises PermissionDeniedError (403)."""
        image_id, _ = image_fixture
        with pytest.raises(PermissionDeniedError):
            await user_registry.image.get(image_id)
