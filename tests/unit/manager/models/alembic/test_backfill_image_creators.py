"""Verifies the customized-image creator backfill against a real database.

Static analysis does not reach the migration's SQL, so the data migration is exercised
here: images carrying every owner-label shape go in, the backfill runs, and the column
it wrote is read back.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any, cast

import pytest
import sqlalchemy as sa
from sqlalchemy import Table

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.image.types import ImageStatus, ImageType
from ai.backend.manager.models.alembic.versions.a3f57c4d90e2_record_a_customized_image_creator import (
    backfill,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.db import HasTable, with_tables

_OWNER_LABEL = "ai.backend.customized-image.owner"
_REGISTRY_NAME = "cr.test.io"

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


@dataclass
class DomainFixture:
    name: DomainName
    id: DomainID


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, _TABLES):
        yield database_connection


@pytest.fixture
async def domain(db: ExtendedAsyncSAEngine) -> DomainFixture:
    domain_id = DomainID(uuid.uuid4())
    domain_name = DomainName(f"test-domain-{uuid.uuid4().hex[:8]}")
    async with db.begin_session() as session:
        session.add(
            DomainRow(
                id=domain_id,
                name=domain_name,
                description="Test domain",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
                allowed_docker_registries=[_REGISTRY_NAME],
                dotfiles=b"",
                integration_id=None,
            )
        )
        session.add(
            UserResourcePolicyRow(
                name="default",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
        )
        await session.commit()
    return DomainFixture(name=domain_name, id=domain_id)


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


async def _add_user(db: ExtendedAsyncSAEngine, domain: DomainFixture) -> uuid.UUID:
    user_uuid = uuid.uuid4()
    async with db.begin_session() as session:
        session.add(
            UserRow(
                uuid=user_uuid,
                username=f"user-{user_uuid.hex[:8]}",
                email=f"{user_uuid.hex[:8]}@test.local",
                password=PasswordInfo(
                    password="test-password",
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=1_000,
                    salt_size=32,
                ),
                need_password_change=False,
                domain_id=domain.id,
                domain_name=domain.name,
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                resource_policy="default",
            )
        )
        await session.commit()
    return user_uuid


async def _add_image(
    db: ExtendedAsyncSAEngine,
    registry_id: ContainerRegistryID,
    tag: str,
    labels: dict[str, Any],
) -> uuid.UUID:
    """An image inserted directly, as one predating the creator column would be."""
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
            type=ImageType.COMPUTE,
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


async def _creator_id(db: ExtendedAsyncSAEngine, image_id: uuid.UUID) -> uuid.UUID | None:
    async with db.begin_readonly_session() as session:
        return cast(
            uuid.UUID | None,
            await session.scalar(sa.select(ImageRow.creator_id).where(ImageRow.id == image_id)),
        )


class TestBackfillImageCreators:
    async def test_a_well_formed_owner_label_names_the_creator(
        self,
        db: ExtendedAsyncSAEngine,
        domain: DomainFixture,
        registry_id: ContainerRegistryID,
    ) -> None:
        user_uuid = await _add_user(db, domain)
        image_id = await _add_image(db, registry_id, "a", {_OWNER_LABEL: f"user:{user_uuid}"})

        await _run_backfill(db)

        assert await _creator_id(db, image_id) == user_uuid

    async def test_an_image_without_the_label_records_nobody(
        self,
        db: ExtendedAsyncSAEngine,
        domain: DomainFixture,
        registry_id: ContainerRegistryID,
    ) -> None:
        image_id = await _add_image(db, registry_id, "a", {})

        await _run_backfill(db)

        assert await _creator_id(db, image_id) is None

    @pytest.mark.parametrize(
        "label_value",
        ["user:not-a-uuid", "user:", "", f"{uuid.uuid4()}"],
    )
    async def test_an_unreadable_owner_label_records_nobody(
        self,
        db: ExtendedAsyncSAEngine,
        domain: DomainFixture,
        registry_id: ContainerRegistryID,
        label_value: str,
    ) -> None:
        image_id = await _add_image(db, registry_id, "a", {_OWNER_LABEL: label_value})

        await _run_backfill(db)

        assert await _creator_id(db, image_id) is None

    async def test_a_label_naming_a_user_who_is_gone_records_nobody(
        self,
        db: ExtendedAsyncSAEngine,
        domain: DomainFixture,
        registry_id: ContainerRegistryID,
    ) -> None:
        image_id = await _add_image(db, registry_id, "a", {_OWNER_LABEL: f"user:{uuid.uuid4()}"})

        await _run_backfill(db)

        assert await _creator_id(db, image_id) is None
