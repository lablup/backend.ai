"""Tests for ImageRow.resolve() method."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from uuid import UUID, uuid4

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.docker import ImageRef
from ai.backend.common.types import ImageAlias
from ai.backend.manager.data.image.types import ImageIdentifier, ImageStatus, ImageType
from ai.backend.manager.errors.image import ImageNotFound
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.image import ImageAliasRow, ImageRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.db import with_tables


class TestImageRowResolve:
    """Tests for ImageRow.resolve()."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
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
    async def registry_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> UUID:
        registry_id = uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
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
            await db_sess.commit()
        return registry_id

    @pytest.fixture
    async def alive_image(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        registry_id: UUID,
    ) -> ImageRow:
        async with db_with_cleanup.begin_session() as db_sess:
            image = ImageRow(
                name="cr.example.com/stable/python:3.11",
                image="python",
                tag="3.11",
                registry="cr.example.com",
                registry_id=registry_id,
                project="stable",
                architecture="x86_64",
                config_digest=f"sha256:{uuid4().hex}",
                size_bytes=500_000,
                type=ImageType.COMPUTE,
                status=ImageStatus.ALIVE,
                labels={},
                resources={},
            )
            db_sess.add(image)
            await db_sess.flush()
            image_id = image.id
            await db_sess.commit()

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            return await db_sess.get_one(ImageRow, image_id)

    @pytest.fixture
    async def deleted_image(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        registry_id: UUID,
    ) -> ImageRow:
        async with db_with_cleanup.begin_session() as db_sess:
            image = ImageRow(
                name="cr.example.com/stable/old-image:1.0",
                image="old-image",
                tag="1.0",
                registry="cr.example.com",
                registry_id=registry_id,
                project="stable",
                architecture="x86_64",
                config_digest=f"sha256:{uuid4().hex}",
                size_bytes=300_000,
                type=ImageType.COMPUTE,
                status=ImageStatus.DELETED,
                labels={},
                resources={},
            )
            db_sess.add(image)
            await db_sess.flush()
            image_id = image.id
            await db_sess.commit()

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            return await db_sess.get_one(ImageRow, image_id)

    @pytest.fixture
    async def aliased_image(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        alive_image: ImageRow,
    ) -> str:
        alias = "my-python"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(ImageAliasRow(alias=alias, image_id=alive_image.id))
            await db_sess.commit()
        return alias

    # ------------------------------------------------------------------
    # Resolve via ImageIdentifier
    # ------------------------------------------------------------------

    async def test_resolve_by_identifier(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        alive_image: ImageRow,
    ) -> None:
        """Resolve an ALIVE image using ImageIdentifier."""
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            result = await ImageRow.resolve(
                db_sess,
                [ImageIdentifier(alive_image.name, alive_image.architecture)],
            )
        assert result.id == alive_image.id

    async def test_resolve_by_identifier_not_found(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        registry_id: UUID,
    ) -> None:
        """Raise ImageNotFound when no image matches the identifier."""
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            with pytest.raises(ImageNotFound):
                await ImageRow.resolve(
                    db_sess,
                    [ImageIdentifier("cr.example.com/stable/nonexistent:latest", "x86_64")],
                )

    # ------------------------------------------------------------------
    # Resolve via ImageAlias
    # ------------------------------------------------------------------

    async def test_resolve_by_alias(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        alive_image: ImageRow,
        aliased_image: str,
    ) -> None:
        """Resolve an image via its alias."""
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            result = await ImageRow.resolve(
                db_sess,
                [ImageAlias(aliased_image)],
            )
        assert result.id == alive_image.id

    async def test_resolve_by_alias_not_found(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        registry_id: UUID,
    ) -> None:
        """Raise ImageNotFound when alias does not exist."""
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            with pytest.raises(ImageNotFound):
                await ImageRow.resolve(db_sess, [ImageAlias("no-such-alias")])

    # ------------------------------------------------------------------
    # Resolve via ImageRef
    # ------------------------------------------------------------------

    async def test_resolve_by_image_ref(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        alive_image: ImageRow,
    ) -> None:
        """Resolve an image via ImageRef."""
        ref = ImageRef(
            name="python",
            project="stable",
            registry="cr.example.com",
            tag="3.11",
            architecture="x86_64",
            is_local=False,
        )
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            result = await ImageRow.resolve(db_sess, [ref])
        assert result.id == alive_image.id

    # ------------------------------------------------------------------
    # filter_by_statuses
    # ------------------------------------------------------------------

    async def test_resolve_deleted_image_excluded_by_default(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        deleted_image: ImageRow,
    ) -> None:
        """DELETED images are NOT resolved when filter_by_statuses is default (ALIVE only)."""
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            with pytest.raises(ImageNotFound):
                await ImageRow.resolve(
                    db_sess,
                    [ImageIdentifier(deleted_image.name, deleted_image.architecture)],
                )

    async def test_resolve_deleted_image_with_explicit_statuses(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        deleted_image: ImageRow,
    ) -> None:
        """DELETED images CAN be resolved when DELETED is included in filter_by_statuses."""
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            result = await ImageRow.resolve(
                db_sess,
                [ImageIdentifier(deleted_image.name, deleted_image.architecture)],
                filter_by_statuses=[ImageStatus.ALIVE, ImageStatus.DELETED],
            )
        assert result.id == deleted_image.id

    # ------------------------------------------------------------------
    # Candidate priority (first match wins)
    # ------------------------------------------------------------------

    async def test_resolve_returns_first_matching_candidate(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        alive_image: ImageRow,
        aliased_image: str,
    ) -> None:
        """When multiple candidates are given, the first matching one is returned."""
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            result = await ImageRow.resolve(
                db_sess,
                [
                    ImageAlias("nonexistent-alias"),
                    ImageIdentifier(alive_image.name, alive_image.architecture),
                    ImageAlias(aliased_image),
                ],
            )
        assert result.id == alive_image.id

    async def test_resolve_all_candidates_fail(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        registry_id: UUID,
    ) -> None:
        """Raise ImageNotFound when none of the candidates match."""
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            with pytest.raises(ImageNotFound):
                await ImageRow.resolve(
                    db_sess,
                    [
                        ImageAlias("no-alias"),
                        ImageIdentifier("no-image:1.0", "x86_64"),
                    ],
                )
