"""Verifies the pending vfolder invitation migration against a real database.

Static analysis does not reach the migration's SQL, so the data migration is exercised
here: folders and invitations go in, the migration runs, and the shares it wrote are
read back.
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
from ai.backend.common.types import QuotaScopeID, ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.entity_share.types import EntityShareStatus
from ai.backend.manager.data.vfolder.types import (
    VFolderInvitationState,
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.models.alembic.versions.c3f8a1d6e920_move_pending_vfolder_invitations_to_shares import (
    move_pending_invitations_to_shares,
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
from ai.backend.manager.models.vfolder.row import VFolderRow
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
legacy_invitations = sa.Table(
    "vfolder_invitations",
    sa.MetaData(),
    sa.Column("id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v7()")),
    sa.Column("permission", postgresql.ENUM("ro", "rw", "wd", name="vfoldermountpermission")),
    sa.Column("inviter", sa.String(length=256)),
    sa.Column("invitee", sa.String(length=256), nullable=False),
    sa.Column(
        "state",
        postgresql.ENUM(
            "pending", "canceled", "accepted", "rejected", name="vfolderinvitationstate"
        ),
    ),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    sa.Column("vfolder", GUID, nullable=False),
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
    legacy_invitations,
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
    """An inviter, the project folder they invite to, and the project it sits in."""

    inviter_id: uuid.UUID
    inviter_email: str
    project_id: uuid.UUID
    vfolder_id: uuid.UUID


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, _TABLES):
        yield database_connection


@pytest.fixture
async def fixture(db: ExtendedAsyncSAEngine) -> Fixture:
    domain_id = DomainID(uuid.uuid4())
    domain_name = DomainName(f"test-domain-{uuid.uuid4().hex[:8]}")
    inviter_id = uuid.uuid4()
    inviter_email = f"{uuid.uuid4().hex[:8]}@test.local"
    project_id = uuid.uuid4()
    vfolder_id = uuid.uuid4()
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
                uuid=inviter_id,
                username="alice",
                email=inviter_email,
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
        session.add(VirtualEntityRow(entity_type="project", entity_id=project_id))
        session.add(
            VFolderRow(
                id=vfolder_id,
                name="shared",
                domain_name=domain_name,
                quota_scope_id=QuotaScopeID.parse(f"project:{project_id}"),
                host="local",
                creator=inviter_email,
                creator_id=inviter_id,
                ownership_type=VFolderOwnershipType.GROUP,
                user=None,
                group=project_id,
                cloneable=False,
                status=VFolderOperationStatus.READY,
            )
        )
        await session.commit()
    return Fixture(
        inviter_id=inviter_id,
        inviter_email=inviter_email,
        project_id=project_id,
        vfolder_id=vfolder_id,
    )


async def _add_invitation(
    db: ExtendedAsyncSAEngine,
    fx: Fixture,
    *,
    invitee: str = "bob@test.local",
    inviter: str | None = None,
    permission: VFolderMountPermission = VFolderMountPermission.READ_ONLY,
    state: VFolderInvitationState = VFolderInvitationState.PENDING,
) -> None:
    async with db.begin() as conn:
        await conn.execute(
            legacy_invitations.insert().values(
                vfolder=fx.vfolder_id,
                inviter=inviter if inviter is not None else fx.inviter_email,
                invitee=invitee,
                permission=permission.value,
                state=state.value,
            )
        )


async def _run(db: ExtendedAsyncSAEngine) -> None:
    async with db.begin() as conn:
        await conn.run_sync(move_pending_invitations_to_shares)


async def _shares(db: ExtendedAsyncSAEngine, vfolder_id: uuid.UUID) -> list[EntityShareRow]:
    async with db.begin_readonly_session() as session:
        return list(
            (
                await session.scalars(
                    sa.select(EntityShareRow).where(EntityShareRow.target_entity_id == vfolder_id)
                )
            ).all()
        )


async def _node_of(
    db: ExtendedAsyncSAEngine, entity_type: str, entity_id: uuid.UUID
) -> uuid.UUID | None:
    async with db.begin_readonly_session() as session:
        node: uuid.UUID | None = await session.scalar(
            sa.select(VirtualEntityRow.id).where(
                VirtualEntityRow.entity_type == entity_type,
                VirtualEntityRow.entity_id == entity_id,
            )
        )
        return node


async def _owners_of(db: ExtendedAsyncSAEngine, node: uuid.UUID) -> set[uuid.UUID]:
    async with db.begin_readonly_session() as session:
        return set(
            (
                await session.scalars(
                    sa.select(EntityMembershipRow.virtual_entity_id).where(
                        EntityMembershipRow.member_entity_id == node
                    )
                )
            ).all()
        )


class TestMovePendingVFolderInvitationsToShares:
    async def test_a_pending_invitation_becomes_a_pending_share(
        self, db: ExtendedAsyncSAEngine, fixture: Fixture
    ) -> None:
        await _add_invitation(db, fixture)

        await _run(db)

        shares = await _shares(db, fixture.vfolder_id)
        assert len(shares) == 1
        share = shares[0]
        assert share.status == EntityShareStatus.PENDING
        assert share.recipient_email == "bob@test.local"
        assert share.sharer_user_id == fixture.inviter_id
        assert share.permission_cap == Permission.READ

    async def test_a_writable_invitation_lends_update(
        self, db: ExtendedAsyncSAEngine, fixture: Fixture
    ) -> None:
        await _add_invitation(db, fixture, permission=VFolderMountPermission.READ_WRITE)

        await _run(db)

        shares = await _shares(db, fixture.vfolder_id)
        assert [share.permission_cap for share in shares] == [_WRITABLE_CAP]

    async def test_answered_invitations_stay_behind(
        self, db: ExtendedAsyncSAEngine, fixture: Fixture
    ) -> None:
        await _add_invitation(
            db, fixture, invitee="accepted@test.local", state=VFolderInvitationState.ACCEPTED
        )
        await _add_invitation(
            db, fixture, invitee="rejected@test.local", state=VFolderInvitationState.REJECTED
        )

        await _run(db)

        assert await _shares(db, fixture.vfolder_id) == []

    async def test_an_unknown_inviter_leaves_no_sharer(
        self, db: ExtendedAsyncSAEngine, fixture: Fixture
    ) -> None:
        await _add_invitation(db, fixture, inviter="gone@test.local")

        await _run(db)

        shares = await _shares(db, fixture.vfolder_id)
        assert [share.sharer_user_id for share in shares] == [None]

    async def test_a_folder_without_a_node_is_put_under_its_project(
        self, db: ExtendedAsyncSAEngine, fixture: Fixture
    ) -> None:
        await _add_invitation(db, fixture)

        await _run(db)

        folder_node = await _node_of(db, "vfolder", fixture.vfolder_id)
        project_node = await _node_of(db, "project", fixture.project_id)
        assert folder_node is not None
        assert project_node in await _owners_of(db, folder_node)
        share = (await _shares(db, fixture.vfolder_id))[0]
        share_node = await _node_of(db, "entity_share", share.id)
        assert share_node is not None
        assert folder_node in await _owners_of(db, share_node)

    async def test_running_twice_changes_nothing(
        self, db: ExtendedAsyncSAEngine, fixture: Fixture
    ) -> None:
        await _add_invitation(db, fixture)

        await _run(db)
        await _run(db)

        assert len(await _shares(db, fixture.vfolder_id)) == 1
