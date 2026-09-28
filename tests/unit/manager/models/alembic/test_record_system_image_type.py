"""Verifies the image-type backfill against a real database.

Static analysis does not reach the migration's SQL, so images carrying every role and
feature label shape go in, the backfill runs, and the type column is read back.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy import Table

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.manager.data.image.types import ImageStatus, ImageType
from ai.backend.manager.models.alembic.versions.b9f2c41ad07e_record_system_image_type_from_labels import (
    backfill,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.db import HasTable, with_tables

_ROLE_LABEL = "ai.backend.role"
_FEATURES_LABEL = "ai.backend.features"
_REGISTRY_NAME = "cr.test.io"

# The images table's inline foreign keys need their targets to exist, even unpopulated.
_TABLES: list[Table | type[HasTable]] = [
    DomainRow,
    UserResourcePolicyRow,
    ProjectResourcePolicyRow,
    KeyPairResourcePolicyRow,
    UserRow,
    KeyPairRow,
    ProjectRow,
    ContainerRegistryRow,
    ImageRow,
]


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, _TABLES):
        yield database_connection


@pytest.fixture
async def registry_id(db: ExtendedAsyncSAEngine) -> ContainerRegistryID:
    registry_id = ContainerRegistryID(uuid.uuid4())
    async with db.begin_session() as session:
        session.add(
            ContainerRegistryRow(
                id=registry_id,
                url=f"https://{_REGISTRY_NAME}",
                registry_name=_REGISTRY_NAME,
                type=ContainerRegistryType.DOCKER,
                project="stable",
                is_global=True,
            )
        )
        await session.commit()
    return registry_id


async def _add_image(
    db: ExtendedAsyncSAEngine,
    registry_id: ContainerRegistryID,
    tag: str,
    labels: dict[str, Any],
    image_type: ImageType = ImageType.COMPUTE,
) -> uuid.UUID:
    """An image inserted directly, as one the scan wrote before the rule existed would be."""
    async with db.begin_session() as session:
        row = ImageRow(
            name=f"{_REGISTRY_NAME}/stable/python:{tag}",
            image="python",
            tag=tag,
            registry=_REGISTRY_NAME,
            registry_id=registry_id,
            project="stable",
            architecture="x86_64",
            config_digest=f"sha256:{uuid.uuid4().hex}",
            size_bytes=1000,
            type=image_type,
            status=ImageStatus.ALIVE,
            accelerators=None,
            labels=labels,
            resources={},
        )
        session.add(row)
        await session.flush()
        image_id = row.id
        await session.commit()
    return image_id


async def _run_backfill(db: ExtendedAsyncSAEngine) -> None:
    async with db.begin() as conn:
        await conn.run_sync(lambda sync_conn: backfill(sync_conn))


async def _type_of(db: ExtendedAsyncSAEngine, image_id: uuid.UUID) -> ImageType:
    async with db.begin_readonly_session() as session:
        return (
            await session.execute(sa.select(ImageRow.type).where(ImageRow.id == image_id))
        ).scalar_one()


class TestRecordSystemImageType:
    @pytest.mark.parametrize(
        ("labels", "expected"),
        [
            pytest.param(
                {_ROLE_LABEL: "SYSTEM"},
                ImageType.SYSTEM,
                id="the-system-role-becomes-a-system-image",
            ),
            pytest.param(
                {_ROLE_LABEL: "SYSTEM", _FEATURES_LABEL: "uid-match private"},
                ImageType.SYSTEM,
                id="the-sftp-server-image-becomes-a-system-image",
            ),
            pytest.param(
                {_FEATURES_LABEL: "uid-match operation"},
                ImageType.SYSTEM,
                id="the-operation-feature-becomes-a-system-image",
            ),
            pytest.param(
                {_ROLE_LABEL: "INFERENCE"},
                ImageType.COMPUTE,
                id="the-inference-role-is-absorbed-into-compute",
            ),
            pytest.param({}, ImageType.COMPUTE, id="an-image-without-labels-stays-compute"),
            pytest.param(
                {_FEATURES_LABEL: "uid-match"},
                ImageType.COMPUTE,
                id="a-feature-list-without-operation-stays-compute",
            ),
            pytest.param(
                {_FEATURES_LABEL: "uid-match operational"},
                ImageType.COMPUTE,
                id="a-feature-merely-starting-with-operation-does-not-match",
            ),
        ],
    )
    async def test_the_labels_decide_the_type(
        self,
        db: ExtendedAsyncSAEngine,
        registry_id: ContainerRegistryID,
        labels: dict[str, Any],
        expected: ImageType,
    ) -> None:
        image_id = await _add_image(db, registry_id, "a", labels)

        await _run_backfill(db)

        assert await _type_of(db, image_id) == expected

    async def test_a_second_run_leaves_the_type_it_wrote(
        self, db: ExtendedAsyncSAEngine, registry_id: ContainerRegistryID
    ) -> None:
        image_id = await _add_image(db, registry_id, "a", {_ROLE_LABEL: "SYSTEM"})

        await _run_backfill(db)
        await _run_backfill(db)

        assert await _type_of(db, image_id) == ImageType.SYSTEM

    async def test_an_image_already_marked_system_is_left_alone(
        self, db: ExtendedAsyncSAEngine, registry_id: ContainerRegistryID
    ) -> None:
        image_id = await _add_image(db, registry_id, "a", {}, image_type=ImageType.SYSTEM)

        await _run_backfill(db)

        assert await _type_of(db, image_id) == ImageType.SYSTEM

    async def test_a_row_left_at_the_deprecated_service_type_becomes_compute(
        self, db: ExtendedAsyncSAEngine, registry_id: ContainerRegistryID
    ) -> None:
        image_id = await _add_image(db, registry_id, "a", {}, image_type=ImageType.SERVICE)

        await _run_backfill(db)

        assert await _type_of(db, image_id) == ImageType.COMPUTE

    async def test_a_service_row_whose_labels_say_system_becomes_system(
        self, db: ExtendedAsyncSAEngine, registry_id: ContainerRegistryID
    ) -> None:
        image_id = await _add_image(
            db, registry_id, "a", {_ROLE_LABEL: "SYSTEM"}, image_type=ImageType.SERVICE
        )

        await _run_backfill(db)

        assert await _type_of(db, image_id) == ImageType.SYSTEM
