"""Which image a reference resolves to through the image read specs."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Collection
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import uuid4

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.image import ImageID
from ai.backend.manager.data.image.types import ImageStatus, ImageType
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.image import ImageAliasRow, ImageRow
from ai.backend.manager.models.image.queriers import ImageQuerier
from ai.backend.manager.models.image.searchers import ReferenceImageSearcher
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.resource_group import ResourceGroupForProjectRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.db import with_tables

# Rows reachable only through string relationships, kept live for configure_mappers().
_ORM_CLUSTER = (
    AgentRow,
    ResourceGroupForProjectRow,
)

_CANONICAL = "cr.example.com/stable/python:3.11"
_BASE_TIME = datetime(2026, 1, 1, tzinfo=UTC)


class AddImage(Protocol):
    async def __call__(
        self,
        name: str,
        *,
        architecture: str = "x86_64",
        status: ImageStatus = ImageStatus.ALIVE,
        project: str | None = "stable",
        created_at: datetime = _BASE_TIME,
    ) -> ImageID: ...


class AddAlias(Protocol):
    async def __call__(self, alias: str, image_id: ImageID) -> None: ...


class ResolveReference(Protocol):
    async def __call__(
        self,
        reference: str,
        architecture: str,
        statuses: Collection[ImageStatus] = (ImageStatus.ALIVE,),
    ) -> list[ImageID]: ...


@pytest.fixture
async def image_db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(
        database_connection,
        [
            # images.creator_id points at users, so the user chain comes first.
            DomainRow,
            UserResourcePolicyRow,
            KeyPairResourcePolicyRow,
            UserRow,
            KeyPairRow,
            ContainerRegistryRow,
            ImageRow,
            ImageAliasRow,
        ],
    ):
        yield database_connection


@pytest.fixture
async def registry_id(image_db: ExtendedAsyncSAEngine) -> ContainerRegistryID:
    registry_id = ContainerRegistryID(uuid4())
    async with image_db.begin_session() as db_sess:
        db_sess.add(
            ContainerRegistryRow(
                id=registry_id,
                url="https://cr.example.com",
                registry_name="cr.example.com",
                type=ContainerRegistryType.DOCKER,
                project="stable",
                is_global=True,
            )
        )
    return registry_id


@pytest.fixture
def add_image(image_db: ExtendedAsyncSAEngine, registry_id: ContainerRegistryID) -> AddImage:
    async def add(
        name: str,
        *,
        architecture: str = "x86_64",
        status: ImageStatus = ImageStatus.ALIVE,
        project: str | None = "stable",
        created_at: datetime = _BASE_TIME,
    ) -> ImageID:
        async with image_db.begin_session() as db_sess:
            row = ImageRow(
                name=name,
                image="python",
                tag="3.11",
                registry="cr.example.com",
                registry_id=registry_id,
                project=project,
                architecture=architecture,
                config_digest=f"sha256:{uuid4().hex}",
                size_bytes=1,
                type=ImageType.COMPUTE,
                status=status,
                labels={},
                resources={},
            )
            row.created_at = created_at
            db_sess.add(row)
            await db_sess.flush()
            return ImageID(row.id)

    return add


@pytest.fixture
def add_alias(image_db: ExtendedAsyncSAEngine) -> AddAlias:
    async def add(alias: str, image_id: ImageID) -> None:
        async with image_db.begin_session() as db_sess:
            db_sess.add(ImageAliasRow(alias=alias, image_id=image_id))

    return add


@pytest.fixture
def ops_provider(image_db: ExtendedAsyncSAEngine) -> V2DBOpsProvider:
    return V2DBOpsProvider(image_db)


@pytest.fixture
def resolve_reference(ops_provider: V2DBOpsProvider) -> ResolveReference:
    async def resolve(
        reference: str,
        architecture: str,
        statuses: Collection[ImageStatus] = (ImageStatus.ALIVE,),
    ) -> list[ImageID]:
        async with ops_provider.read_ops() as r:
            result = await r.search_in_global(
                ReferenceImageSearcher(reference, architecture, statuses)
            )
        return [item.id for item in result.items]

    return resolve


class TestImageSearcherByReference:
    async def test_canonical_for_the_architecture_matches(
        self, add_image: AddImage, resolve_reference: ResolveReference
    ) -> None:
        image_id = await add_image(_CANONICAL)

        assert await resolve_reference(_CANONICAL, "x86_64") == [image_id]

    async def test_canonical_for_another_architecture_does_not_match(
        self, add_image: AddImage, resolve_reference: ResolveReference
    ) -> None:
        await add_image(_CANONICAL, architecture="aarch64")

        assert await resolve_reference(_CANONICAL, "x86_64") == []

    async def test_alias_matches_regardless_of_architecture(
        self, add_image: AddImage, add_alias: AddAlias, resolve_reference: ResolveReference
    ) -> None:
        image_id = await add_image(_CANONICAL, architecture="aarch64")
        await add_alias("my-python", image_id)

        assert await resolve_reference("my-python", "x86_64") == [image_id]

    async def test_unknown_reference_matches_nothing(
        self, add_image: AddImage, resolve_reference: ResolveReference
    ) -> None:
        await add_image(_CANONICAL)

        assert await resolve_reference("no-such-image", "x86_64") == []

    async def test_deleted_image_is_excluded_when_only_alive_is_allowed(
        self, add_image: AddImage, resolve_reference: ResolveReference
    ) -> None:
        await add_image(_CANONICAL, status=ImageStatus.DELETED)

        assert await resolve_reference(_CANONICAL, "x86_64") == []

    async def test_deleted_image_matches_when_deleted_is_allowed(
        self, add_image: AddImage, resolve_reference: ResolveReference
    ) -> None:
        image_id = await add_image(_CANONICAL, status=ImageStatus.DELETED)

        assert await resolve_reference(
            _CANONICAL, "x86_64", (ImageStatus.ALIVE, ImageStatus.DELETED)
        ) == [image_id]

    async def test_canonical_match_wins_over_an_older_alias_match(
        self, add_image: AddImage, add_alias: AddAlias, resolve_reference: ResolveReference
    ) -> None:
        aliased_id = await add_image("cr.example.com/stable/other:1.0")
        await add_alias(_CANONICAL, aliased_id)
        canonical_id = await add_image(_CANONICAL, created_at=_BASE_TIME + timedelta(hours=1))

        assert await resolve_reference(_CANONICAL, "x86_64") == [canonical_id]

    async def test_alive_wins_over_an_older_deleted_duplicate(
        self, add_image: AddImage, resolve_reference: ResolveReference
    ) -> None:
        await add_image(_CANONICAL, status=ImageStatus.DELETED, project=None)
        alive_id = await add_image(
            _CANONICAL, project=None, created_at=_BASE_TIME + timedelta(hours=1)
        )

        assert await resolve_reference(
            _CANONICAL, "x86_64", (ImageStatus.ALIVE, ImageStatus.DELETED)
        ) == [alive_id]

    async def test_oldest_wins_among_alive_duplicates(
        self, add_image: AddImage, resolve_reference: ResolveReference
    ) -> None:
        await add_image(_CANONICAL, project=None, created_at=_BASE_TIME + timedelta(hours=1))
        oldest_id = await add_image(_CANONICAL, project=None)

        assert await resolve_reference(_CANONICAL, "x86_64") == [oldest_id]


class TestImageQuerier:
    async def test_reads_the_image_by_id(
        self, add_image: AddImage, ops_provider: V2DBOpsProvider
    ) -> None:
        image_id = await add_image(_CANONICAL)

        async with ops_provider.read_ops() as r:
            data = await r.query_data(ImageQuerier(image_id))

        assert data is not None
        assert data.id == image_id

    async def test_unknown_id_reads_nothing(
        self, add_image: AddImage, ops_provider: V2DBOpsProvider
    ) -> None:
        await add_image(_CANONICAL)

        async with ops_provider.read_ops() as r:
            data = await r.query_data(ImageQuerier(ImageID(uuid4())))

        assert data is None
