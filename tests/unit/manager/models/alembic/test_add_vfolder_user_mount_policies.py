"""Verifies the legacy mount row copy of the vfolder user mount policy migration.

Folders and their legacy ``vfolder_permissions`` rows go in, the copy runs, and the
policy rows and accepted shares it wrote are read back.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest
import sqlalchemy as sa
from sqlalchemy import Table
from sqlalchemy.dialects import postgresql

from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.types import (
    QuotaScopeID,
    ResourceSlot,
    VFolderHostPermissionMap,
    VFolderMountPolicy,
)
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.entity_share.types import EntityShareStatus
from ai.backend.manager.data.vfolder.types import (
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.models.alembic.versions.e5b8d3f0a129_add_vfolder_user_mount_policies import (
    copy_legacy_mount_rows,
)
from ai.backend.manager.models.base import GUID
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.entity_share.row import EntityShareRow
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
from ai.backend.manager.models.vfolder.row import VFolderRow, VFolderUserMountPolicyRow
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.entity_membership_field import (
    EntityMembershipFieldRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.testutils.db import HasTable, with_tables

# The table the migration copies from, gone from the models after it ran.
legacy_permissions = sa.Table(
    "vfolder_permissions",
    sa.MetaData(),
    sa.Column("id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v7()")),
    sa.Column("permission", postgresql.ENUM("ro", "rw", "wd", name="vfoldermountpermission")),
    sa.Column("vfolder", GUID, nullable=False),
    sa.Column("user", GUID, nullable=False),
)

_TABLES: list[Table | type[HasTable]] = [
    DomainRow,
    UserResourcePolicyRow,
    ProjectResourcePolicyRow,
    KeyPairResourcePolicyRow,
    UserRow,
    KeyPairRow,
    ProjectRow,
    VFolderRow,
    legacy_permissions,
    VFolderUserMountPolicyRow,
    VirtualEntityRow,
    ScopeBindingRow,
    EntityMembershipRow,
    EntityMembershipCapRow,
    EntityMembershipFieldRow,
    EntityShareRow,
]

_WRITABLE_CAP = Permission.READ | Permission.UPDATE | Permission.SOFT_DELETE


@dataclass
class Fixture:
    """An owner, a guest, the owner's personal folder and a model store folder."""

    owner_id: uuid.UUID
    guest_id: uuid.UUID
    personal_folder_id: uuid.UUID
    model_store_folder_id: uuid.UUID


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, _TABLES):
        yield database_connection


def _user(user_id: uuid.UUID, domain_id: DomainID, domain_name: DomainName) -> UserRow:
    return UserRow(
        uuid=user_id,
        username=uuid.uuid4().hex[:8],
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


@pytest.fixture
async def fixture(db: ExtendedAsyncSAEngine) -> Fixture:
    domain_id = DomainID(uuid.uuid4())
    domain_name = DomainName(f"test-domain-{uuid.uuid4().hex[:8]}")
    owner_id = uuid.uuid4()
    guest_id = uuid.uuid4()
    personal_project_id = uuid.uuid4()
    model_store_id = uuid.uuid4()
    personal_folder_id = uuid.uuid4()
    model_store_folder_id = uuid.uuid4()
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
        session.add(_user(owner_id, domain_id, domain_name))
        session.add(_user(guest_id, domain_id, domain_name))
        await session.commit()
    async with db.begin_session() as session:
        session.add(
            ProjectRow(
                id=personal_project_id,
                name=f"personal-{owner_id.hex[:8]}",
                domain_name=domain_name,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
                resource_policy="default",
                type=ProjectType.PERSONAL,
                creator_id=owner_id,
            )
        )
        session.add(
            ProjectRow(
                id=model_store_id,
                name="model-store",
                domain_name=domain_name,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
                resource_policy="default",
                type=ProjectType.MODEL_STORE,
                creator_id=None,
            )
        )
        session.add(
            VFolderRow(
                id=personal_folder_id,
                name="mine",
                domain_name=domain_name,
                quota_scope_id=QuotaScopeID.parse(f"user:{owner_id}"),
                host="local",
                creator_id=owner_id,
                ownership_type=VFolderOwnershipType.USER,
                user=owner_id,
                group=personal_project_id,
                cloneable=False,
                status=VFolderOperationStatus.READY,
            )
        )
        session.add(
            VFolderRow(
                id=model_store_folder_id,
                name="model",
                domain_name=domain_name,
                quota_scope_id=QuotaScopeID.parse(f"project:{model_store_id}"),
                host="local",
                creator_id=owner_id,
                ownership_type=VFolderOwnershipType.GROUP,
                user=None,
                group=model_store_id,
                cloneable=False,
                status=VFolderOperationStatus.READY,
            )
        )
        await session.commit()
    return Fixture(
        owner_id=owner_id,
        guest_id=guest_id,
        personal_folder_id=personal_folder_id,
        model_store_folder_id=model_store_folder_id,
    )


async def _add_legacy_row(
    db: ExtendedAsyncSAEngine,
    vfolder_id: uuid.UUID,
    user_id: uuid.UUID,
    permission: str,
) -> None:
    async with db.begin() as conn:
        await conn.execute(
            legacy_permissions.insert().values(
                vfolder=vfolder_id, user=user_id, permission=permission
            )
        )


async def _run(db: ExtendedAsyncSAEngine) -> None:
    async with db.begin() as conn:
        await conn.run_sync(copy_legacy_mount_rows)


async def _policies(
    db: ExtendedAsyncSAEngine, vfolder_id: uuid.UUID
) -> dict[uuid.UUID, VFolderMountPolicy]:
    async with db.begin_readonly_session() as session:
        rows = await session.scalars(
            sa.select(VFolderUserMountPolicyRow).where(
                VFolderUserMountPolicyRow.vfolder_id == vfolder_id
            )
        )
        return {row.user_id: row.permission for row in rows.all()}


async def _shares(db: ExtendedAsyncSAEngine, vfolder_id: uuid.UUID) -> list[EntityShareRow]:
    async with db.begin_readonly_session() as session:
        rows = await session.scalars(
            sa.select(EntityShareRow).where(EntityShareRow.target_entity_id == vfolder_id)
        )
        return list(rows.all())


class TestCopyLegacyMountRows:
    async def test_a_legacy_row_becomes_a_policy_with_wd_folded(
        self, db: ExtendedAsyncSAEngine, fixture: Fixture
    ) -> None:
        await _add_legacy_row(db, fixture.personal_folder_id, fixture.guest_id, "wd")

        await _run(db)

        assert await _policies(db, fixture.personal_folder_id) == {
            fixture.guest_id: VFolderMountPolicy.READ_WRITE
        }

    async def test_the_widest_of_duplicate_rows_wins(
        self, db: ExtendedAsyncSAEngine, fixture: Fixture
    ) -> None:
        await _add_legacy_row(db, fixture.personal_folder_id, fixture.guest_id, "ro")
        await _add_legacy_row(db, fixture.personal_folder_id, fixture.guest_id, "rw")

        await _run(db)

        assert await _policies(db, fixture.personal_folder_id) == {
            fixture.guest_id: VFolderMountPolicy.READ_WRITE
        }

    async def test_the_owners_own_row_is_dropped(
        self, db: ExtendedAsyncSAEngine, fixture: Fixture
    ) -> None:
        await _add_legacy_row(db, fixture.personal_folder_id, fixture.owner_id, "rw")

        await _run(db)

        assert await _policies(db, fixture.personal_folder_id) == {}
        assert await _shares(db, fixture.personal_folder_id) == []

    async def test_a_model_store_maker_keeps_read_write(
        self, db: ExtendedAsyncSAEngine, fixture: Fixture
    ) -> None:
        await _add_legacy_row(db, fixture.model_store_folder_id, fixture.owner_id, "ro")

        await _run(db)

        assert await _policies(db, fixture.model_store_folder_id) == {
            fixture.owner_id: VFolderMountPolicy.READ_WRITE
        }

    async def test_a_legacy_row_records_an_accepted_share(
        self, db: ExtendedAsyncSAEngine, fixture: Fixture
    ) -> None:
        await _add_legacy_row(db, fixture.personal_folder_id, fixture.guest_id, "ro")

        await _run(db)

        shares = await _shares(db, fixture.personal_folder_id)
        assert len(shares) == 1
        share = shares[0]
        assert share.status == EntityShareStatus.ACCEPTED
        assert share.recipient_entity_id == fixture.guest_id
        assert share.sharer_user_id == fixture.owner_id
        assert share.permission_cap == Permission.READ

    async def test_a_writable_row_lends_update(
        self, db: ExtendedAsyncSAEngine, fixture: Fixture
    ) -> None:
        await _add_legacy_row(db, fixture.personal_folder_id, fixture.guest_id, "rw")

        await _run(db)

        assert [s.permission_cap for s in await _shares(db, fixture.personal_folder_id)] == [
            _WRITABLE_CAP
        ]

    async def test_running_twice_writes_nothing_more(
        self, db: ExtendedAsyncSAEngine, fixture: Fixture
    ) -> None:
        await _add_legacy_row(db, fixture.personal_folder_id, fixture.guest_id, "ro")

        await _run(db)
        await _run(db)

        assert len(await _shares(db, fixture.personal_folder_id)) == 1
        assert len(await _policies(db, fixture.personal_folder_id)) == 1
