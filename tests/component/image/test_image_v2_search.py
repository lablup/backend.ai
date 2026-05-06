"""Component tests for the v2 admin image search REST endpoint (POST /v2/images/search).

Exercises the v2 SDK ``V2ImageClient.admin_search`` against a real aiohttp server,
covering the ``ImageFilterInputDTO`` fields surfaced through ``ImageV2FilterGQL``.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

import pytest
import yarl

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.exceptions import PermissionDeniedError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.query import UUIDFilter
from ai.backend.common.dto.manager.v2.image.request import (
    AdminSearchImagesInput,
    ImageFilterInputDTO,
)
from ai.backend.common.dto.manager.v2.image.response import AdminSearchImagesPayload

if TYPE_CHECKING:
    from tests.component.conftest import ServerInfo, UserFixtureData
    from tests.component.image.conftest import ImageFactoryHelper


@pytest.fixture()
async def admin_v2_registry(
    server: ServerInfo,
    admin_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
    registry = await V2ClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(
            access_key=admin_user_fixture.keypair.access_key,
            secret_key=admin_user_fixture.keypair.secret_key,
        ),
    )
    try:
        yield registry
    finally:
        await registry.close()


@pytest.fixture()
async def user_v2_registry(
    server: ServerInfo,
    regular_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
    registry = await V2ClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(
            access_key=regular_user_fixture.keypair.access_key,
            secret_key=regular_user_fixture.keypair.secret_key,
        ),
    )
    try:
        yield registry
    finally:
        await registry.close()


class TestV2AdminSearchImages:
    """Sanity coverage for the v2 admin_search endpoint."""

    async def test_no_filter_returns_seeded_image(
        self,
        admin_v2_registry: V2ClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """Calling admin_search without a filter returns the pre-seeded image."""
        image_id, _ = image_fixture
        result = await admin_v2_registry.image.admin_search(AdminSearchImagesInput())
        assert isinstance(result, AdminSearchImagesPayload)
        assert result.total_count >= 1
        assert image_id in [item.id for item in result.items]


class TestV2AdminSearchImagesByID:
    """Filter ``ImageV2Filter.id`` (the BA-5939 fix)."""

    async def test_filter_id_equals_returns_only_target(
        self,
        admin_v2_registry: V2ClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """``id.equals`` returns exactly the matching image and no others."""
        image_id, helper = image_fixture
        await helper.create(name_suffix="other-image")

        result = await admin_v2_registry.image.admin_search(
            AdminSearchImagesInput(filter=ImageFilterInputDTO(id=UUIDFilter(equals=image_id))),
        )
        assert isinstance(result, AdminSearchImagesPayload)
        assert result.total_count == 1
        assert [item.id for item in result.items] == [image_id]

    async def test_filter_id_in_returns_all_matches(
        self,
        admin_v2_registry: V2ClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """``id.in_`` returns every image whose id is in the list."""
        image_id, helper = image_fixture
        second_id = await helper.create(name_suffix="second-image")
        third_id = await helper.create(name_suffix="third-image")

        result = await admin_v2_registry.image.admin_search(
            AdminSearchImagesInput(
                filter=ImageFilterInputDTO(id=UUIDFilter(in_=[image_id, second_id])),
            ),
        )
        assert isinstance(result, AdminSearchImagesPayload)
        found_ids = {item.id for item in result.items}
        assert found_ids == {image_id, second_id}
        assert third_id not in found_ids

    async def test_filter_id_no_match_returns_empty(
        self,
        admin_v2_registry: V2ClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """``id.equals`` with a random UUID returns no items."""
        result = await admin_v2_registry.image.admin_search(
            AdminSearchImagesInput(filter=ImageFilterInputDTO(id=UUIDFilter(equals=uuid.uuid4()))),
        )
        assert isinstance(result, AdminSearchImagesPayload)
        assert result.total_count == 0
        assert result.items == []

    async def test_filter_id_not_equals_excludes_target(
        self,
        admin_v2_registry: V2ClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """``id.not_equals`` returns every image except the excluded one."""
        image_id, helper = image_fixture
        other_id = await helper.create(name_suffix="other-image")

        result = await admin_v2_registry.image.admin_search(
            AdminSearchImagesInput(
                filter=ImageFilterInputDTO(id=UUIDFilter(not_equals=image_id)),
            ),
        )
        assert isinstance(result, AdminSearchImagesPayload)
        found_ids = {item.id for item in result.items}
        assert image_id not in found_ids
        assert other_id in found_ids

    async def test_filter_id_not_in_excludes_targets(
        self,
        admin_v2_registry: V2ClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """``id.not_in`` returns every image whose id is outside the list."""
        image_id, helper = image_fixture
        excluded_id = await helper.create(name_suffix="excluded-image")
        kept_id = await helper.create(name_suffix="kept-image")

        result = await admin_v2_registry.image.admin_search(
            AdminSearchImagesInput(
                filter=ImageFilterInputDTO(id=UUIDFilter(not_in=[image_id, excluded_id])),
            ),
        )
        assert isinstance(result, AdminSearchImagesPayload)
        found_ids = {item.id for item in result.items}
        assert image_id not in found_ids
        assert excluded_id not in found_ids
        assert kept_id in found_ids


class TestV2AdminSearchImagesPermissions:
    """Endpoint is mounted under ``superadmin_required`` middleware."""

    async def test_regular_user_cannot_admin_search(
        self,
        user_v2_registry: V2ClientRegistry,
        image_fixture: tuple[uuid.UUID, ImageFactoryHelper],
    ) -> None:
        """A non-admin keypair receives PermissionDeniedError (403)."""
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.image.admin_search(AdminSearchImagesInput())
