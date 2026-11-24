"""Tests for removing an image from its registry through ImageRepository."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.image import ImageID
from ai.backend.manager.container_registry.harbor import HarborRegistry_v2
from ai.backend.manager.data.image.types import ImageStatus, ImageType
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.image.repository import ImageRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.db import with_tables


class TestUntagImageFromRegistry:
    @pytest.fixture
    async def db_with_image_tables(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                UserResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                KeyPairRow,
                ContainerRegistryRow,
                ImageRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def forgotten_image_id(self, db_with_image_tables: ExtendedAsyncSAEngine) -> ImageID:
        async with db_with_image_tables.begin_session() as session:
            registry = ContainerRegistryRow(
                id=ContainerRegistryID(uuid4()),
                url="https://harbor.example.com",
                registry_name="harbor.example.com",
                type=ContainerRegistryType.HARBOR2,
                project="stable",
                is_global=True,
            )
            session.add(registry)
            await session.flush()
            image = ImageRow(
                name="harbor.example.com/stable/python:3.13",
                image="stable/python",
                tag="3.13",
                registry="harbor.example.com",
                registry_id=registry.id,
                project="stable",
                architecture="x86_64",
                config_digest=f"sha256:{uuid4().hex}",
                size_bytes=1000000,
                type=ImageType.COMPUTE,
                status=ImageStatus.DELETED,
                accelerators=None,
                labels={},
                resources={},
            )
            session.add(image)
            await session.flush()
            return image.id

    @pytest.fixture
    def image_repository(self, db_with_image_tables: ExtendedAsyncSAEngine) -> ImageRepository:
        return ImageRepository(
            db=db_with_image_tables,
            ops_provider=V2DBOpsProvider(db_with_image_tables),
            valkey_image=MagicMock(),
            config_provider=MagicMock(),
        )

    async def test_a_forgotten_image_is_removed_from_its_registry(
        self, image_repository: ImageRepository, forgotten_image_id: ImageID
    ) -> None:
        with patch.object(HarborRegistry_v2, "untag", AsyncMock()) as untag:
            untagged_image = await image_repository.untag_image_from_registry(forgotten_image_id)

        assert untagged_image.id == forgotten_image_id
        untag.assert_awaited_once_with(untagged_image.image_ref)
