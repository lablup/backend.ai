"""Verifies the value mapping of the vfolder default mount permission migration.

The tables are made in their current shape and the legacy ``permission`` column is put
back beside the new one, so the migration's two data statements can be run against
real rows.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa
from sqlalchemy import Table

from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.types import (
    QuotaScopeID,
    ResourceSlot,
    VFolderHostPermissionMap,
    VFolderMountPolicy,
)
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.vfolder.types import (
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.models.alembic.versions.d4a7c2e9f018_replace_vfolder_permission_with_default_mount import (
    FILL_DEFAULT_MOUNT_PERMISSION,
    RESTORE_PERMISSION,
)
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project import ProjectRow, ProjectType
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder.row import VFolderPermissionRow, VFolderRow
from ai.backend.testutils.db import HasTable, with_tables

_TABLES: list[Table | type[HasTable]] = [
    DomainRow,
    UserResourcePolicyRow,
    ProjectResourcePolicyRow,
    KeyPairResourcePolicyRow,
    UserRow,
    KeyPairRow,
    ProjectRow,
    VFolderRow,
    # Creating this table creates the legacy enum type the restored column uses.
    VFolderPermissionRow,
]


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, _TABLES):
        async with database_connection.begin() as conn:
            await conn.execute(
                sa.text(
                    "ALTER TABLE vfolders ADD COLUMN IF NOT EXISTS permission vfoldermountpermission"
                )
            )
        yield database_connection


@pytest.fixture
async def folders(db: ExtendedAsyncSAEngine) -> dict[str, uuid.UUID]:
    """A personal folder and four project folders, keyed by the legacy value each holds."""
    domain_id = DomainID(uuid.uuid4())
    domain_name = DomainName(f"test-domain-{uuid.uuid4().hex[:8]}")
    user_id = uuid.uuid4()
    project_id = uuid.uuid4()
    ids = {key: uuid.uuid4() for key in ("personal", "ro", "rw", "wd", "null")}
    async with db.begin_session() as session:
        session.add(
            DomainRow(
                id=domain_id,
                name=domain_name,
                description="Test domain",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
                allowed_docker_registries=[],
                dotfiles=b"",
                integration_id=None,
            )
        )
        session.add(
            ProjectResourcePolicyRow(
                name="default",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
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
        session.add(
            UserRow(
                uuid=user_id,
                username="alice",
                email=f"{uuid.uuid4().hex[:8]}@test.local",
                password=PasswordInfo(
                    password="test-password",
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=1_000,
                    salt_size=32,
                ),
                need_password_change=False,
                domain_id=domain_id,
                domain_name=domain_name,
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                resource_policy="default",
            )
        )
        await session.commit()
    async with db.begin_session() as session:
        session.add(
            ProjectRow(
                id=project_id,
                name="team",
                domain_name=domain_name,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
                resource_policy="default",
                type=ProjectType.GENERAL,
                creator_id=None,
            )
        )
        session.add(
            VFolderRow(
                id=ids["personal"],
                name="mine",
                domain_name=domain_name,
                quota_scope_id=QuotaScopeID.parse(f"user:{user_id}"),
                host="local",
                creator_id=user_id,
                ownership_type=VFolderOwnershipType.USER,
                user=user_id,
                group=project_id,
                cloneable=False,
                status=VFolderOperationStatus.READY,
            )
        )
        for key in ("ro", "rw", "wd", "null"):
            session.add(
                VFolderRow(
                    id=ids[key],
                    name=f"shared-{key}",
                    domain_name=domain_name,
                    quota_scope_id=QuotaScopeID.parse(f"project:{project_id}"),
                    host="local",
                    creator_id=user_id,
                    ownership_type=VFolderOwnershipType.GROUP,
                    user=None,
                    group=project_id,
                    cloneable=False,
                    status=VFolderOperationStatus.READY,
                )
            )
        await session.commit()
    async with db.begin() as conn:
        await conn.execute(
            sa.text("UPDATE vfolders SET permission = 'rw' WHERE id = :id"), {"id": ids["personal"]}
        )
        for key in ("ro", "rw", "wd"):
            await conn.execute(
                sa.text(f"UPDATE vfolders SET permission = '{key}' WHERE id = :id"),
                {"id": ids[key]},
            )
    return ids


async def _default_of(db: ExtendedAsyncSAEngine, vfolder_id: uuid.UUID) -> str | None:
    async with db.begin_readonly() as conn:
        value: str | None = await conn.scalar(
            sa.text("SELECT default_mount_permission FROM vfolders WHERE id = :id"),
            {"id": vfolder_id},
        )
        return value


async def _permission_of(db: ExtendedAsyncSAEngine, vfolder_id: uuid.UUID) -> str | None:
    async with db.begin_readonly() as conn:
        value: str | None = await conn.scalar(
            sa.text("SELECT permission::text FROM vfolders WHERE id = :id"), {"id": vfolder_id}
        )
        return value


class TestReplaceVFolderPermission:
    async def test_a_personal_folder_defaults_to_none(
        self, db: ExtendedAsyncSAEngine, folders: dict[str, uuid.UUID]
    ) -> None:
        async with db.begin() as conn:
            await conn.execute(FILL_DEFAULT_MOUNT_PERMISSION)

        assert await _default_of(db, folders["personal"]) == VFolderMountPolicy.NONE.value

    async def test_a_project_folder_keeps_its_value_with_wd_folded(
        self, db: ExtendedAsyncSAEngine, folders: dict[str, uuid.UUID]
    ) -> None:
        async with db.begin() as conn:
            await conn.execute(FILL_DEFAULT_MOUNT_PERMISSION)

        assert await _default_of(db, folders["ro"]) == VFolderMountPolicy.READ_ONLY.value
        assert await _default_of(db, folders["rw"]) == VFolderMountPolicy.READ_WRITE.value
        assert await _default_of(db, folders["wd"]) == VFolderMountPolicy.READ_WRITE.value
        assert await _default_of(db, folders["null"]) == VFolderMountPolicy.READ_WRITE.value

    async def test_downgrade_restores_ro_and_rw(
        self, db: ExtendedAsyncSAEngine, folders: dict[str, uuid.UUID]
    ) -> None:
        async with db.begin() as conn:
            await conn.execute(
                sa.text("UPDATE vfolders SET default_mount_permission = 'none' WHERE id = :id"),
                {"id": folders["personal"]},
            )
            await conn.execute(
                sa.text("UPDATE vfolders SET default_mount_permission = 'ro' WHERE id = :id"),
                {"id": folders["ro"]},
            )
            await conn.execute(RESTORE_PERMISSION)

        assert await _permission_of(db, folders["personal"]) == "rw"
        assert await _permission_of(db, folders["ro"]) == "ro"
