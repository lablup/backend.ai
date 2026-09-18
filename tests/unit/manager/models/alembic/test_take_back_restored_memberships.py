"""Runs the restored-membership cleanup against a real database and reads the rows back.

The database is shaped like one `f4a1c9d20b73` ran on while it still read
`association_groups_users`: its writes share one timestamp, the preset roles' permission
rows among them.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Final

import pytest
import sqlalchemy as sa
from sqlalchemy import Table

from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.data.permission.types import RoleStatus
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.permission.types import RoleSource
from ai.backend.manager.models.alembic.versions.f345b344d526_take_back_memberships_restored_from_association_groups_users import (
    take_back_restored_memberships,
)
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.project import ProjectRow, ProjectType
from ai.backend.manager.models.project.row import AssocGroupUserRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
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

_TABLES: list[Table | type[HasTable]] = [
    DomainRow,
    UserResourcePolicyRow,
    ProjectResourcePolicyRow,
    KeyPairResourcePolicyRow,
    UserRow,
    ProjectRow,
    AssocGroupUserRow,
    VirtualEntityRow,
    EntityMembershipRow,
    EntityMembershipCapRow,
    EntityMembershipFieldRow,
    ScopeBindingRow,
    RolePresetRow,
    RoleRow,
    PermissionRow,
    UserRoleRow,
]

# When the old revision ran, and a later moment the runtime wrote at.
_MIGRATED_AT: Final = datetime(2026, 9, 10, 12, 0, tzinfo=UTC)
_RUNTIME_AT: Final = _MIGRATED_AT + timedelta(days=3)


@dataclass
class _Project:
    id: uuid.UUID
    node: uuid.UUID
    member_role: uuid.UUID


@dataclass
class _Fixture:
    project: _Project
    domain_id: DomainID
    domain_name: DomainName


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, _TABLES):
        yield database_connection


@pytest.fixture
async def fixture(db: ExtendedAsyncSAEngine) -> _Fixture:
    """A project with its auto_assign preset role, whose permission rows the old revision
    wrote at `_MIGRATED_AT`."""
    domain_id = DomainID(uuid.uuid4())
    domain_name = DomainName(f"test-domain-{uuid.uuid4().hex[:8]}")
    project_id = uuid.uuid4()
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
                name="default", max_vfolder_count=0, max_quota_scope_size=-1, max_network_count=3
            )
        )
        session.add(
            UserResourcePolicyRow(
                name="default",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=1,
                max_customized_image_count=0,
            )
        )
        await session.flush()
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
        node = VirtualEntityRow(entity_type="project", entity_id=project_id)
        session.add(node)
        preset = RolePresetRow(name="project_member", scope_type="project", auto_assign=True)
        session.add(preset)
        await session.flush()
        role = RoleRow(
            name=f"project_member-{str(project_id)[:8]}",
            source=RoleSource.SYSTEM,
            status=RoleStatus.ACTIVE,
            auto_assign=True,
            role_preset_id=preset.id,
            scope_type="project",
            scope_id=project_id,
        )
        session.add(role)
        await session.flush()
        session.add(
            PermissionRow(
                role_id=role.id, entity_type="vfolder", permission=1, created_at=_MIGRATED_AT
            )
        )
        project = _Project(id=project_id, node=node.id, member_role=role.id)
    return _Fixture(project=project, domain_id=domain_id, domain_name=domain_name)


async def _add_user(
    db: ExtendedAsyncSAEngine,
    fx: _Fixture,
    *,
    edge_at: datetime | None = None,
    capped: bool = True,
    granted_at: datetime | None = None,
    in_legacy_roster: bool = True,
) -> uuid.UUID:
    """A user with a node, and on request the project's roster edge written at `edge_at`,
    its member role granted at `granted_at`, and a row in `association_groups_users`."""
    user_id = uuid.uuid4()
    async with db.begin_session() as session:
        session.add(
            UserRow(
                uuid=user_id,
                username=f"u-{user_id.hex[:8]}",
                email=f"{user_id.hex[:8]}@test.local",
                password=PasswordInfo(
                    password="test-password",
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=1_000,
                    salt_size=32,
                ),
                need_password_change=False,
                domain_id=fx.domain_id,
                domain_name=fx.domain_name,
                resource_policy="default",
            )
        )
        node = VirtualEntityRow(entity_type="user", entity_id=user_id)
        session.add(node)
        await session.flush()
        if in_legacy_roster:
            session.add(AssocGroupUserRow(user_id=user_id, group_id=fx.project.id))
        if edge_at is not None:
            session.add(
                EntityMembershipRow(
                    virtual_entity_id=fx.project.node,
                    member_entity_id=node.id,
                    capped=capped,
                    created_at=edge_at,
                )
            )
        if granted_at is not None:
            session.add(
                UserRoleRow(user_id=user_id, role_id=fx.project.member_role, granted_at=granted_at)
            )
    return user_id


async def _run(db: ExtendedAsyncSAEngine) -> None:
    async with db.begin() as conn:
        await conn.run_sync(take_back_restored_memberships)


async def _on_roster(db: ExtendedAsyncSAEngine, fx: _Fixture, user_id: uuid.UUID) -> bool:
    async with db.begin_readonly_session() as session:
        found = await session.scalar(
            sa.select(sa.func.count())
            .select_from(EntityMembershipRow)
            .join(VirtualEntityRow, VirtualEntityRow.id == EntityMembershipRow.member_entity_id)
            .where(
                EntityMembershipRow.virtual_entity_id == fx.project.node,
                VirtualEntityRow.entity_id == user_id,
            )
        )
    return bool(found)


async def _holds_member_role(db: ExtendedAsyncSAEngine, fx: _Fixture, user_id: uuid.UUID) -> bool:
    async with db.begin_readonly_session() as session:
        found = await session.scalar(
            sa.select(sa.func.count())
            .select_from(UserRoleRow)
            .where(UserRoleRow.user_id == user_id, UserRoleRow.role_id == fx.project.member_role)
        )
    return bool(found)


class TestTakeBackRestoredMemberships:
    async def test_a_membership_the_old_revision_restored_goes_with_its_roles(
        self, db: ExtendedAsyncSAEngine, fixture: _Fixture
    ) -> None:
        user_id = await _add_user(db, fixture, edge_at=_MIGRATED_AT, granted_at=_MIGRATED_AT)

        await _run(db)

        assert not await _on_roster(db, fixture, user_id)
        assert not await _holds_member_role(db, fixture, user_id)

    async def test_a_role_granted_at_another_time_stays(
        self, db: ExtendedAsyncSAEngine, fixture: _Fixture
    ) -> None:
        user_id = await _add_user(db, fixture, edge_at=_MIGRATED_AT, granted_at=_RUNTIME_AT)

        await _run(db)

        assert not await _on_roster(db, fixture, user_id)
        assert await _holds_member_role(db, fixture, user_id)

    async def test_a_membership_the_runtime_wrote_stays(
        self, db: ExtendedAsyncSAEngine, fixture: _Fixture
    ) -> None:
        user_id = await _add_user(db, fixture, edge_at=_RUNTIME_AT, granted_at=_RUNTIME_AT)

        await _run(db)

        assert await _on_roster(db, fixture, user_id)
        assert await _holds_member_role(db, fixture, user_id)

    async def test_a_moved_own_edge_stays(
        self, db: ExtendedAsyncSAEngine, fixture: _Fixture
    ) -> None:
        user_id = await _add_user(
            db, fixture, edge_at=_MIGRATED_AT, capped=False, granted_at=_MIGRATED_AT
        )

        await _run(db)

        assert await _on_roster(db, fixture, user_id)
        assert await _holds_member_role(db, fixture, user_id)

    async def test_a_member_absent_from_association_groups_users_stays(
        self, db: ExtendedAsyncSAEngine, fixture: _Fixture
    ) -> None:
        user_id = await _add_user(
            db, fixture, edge_at=_MIGRATED_AT, granted_at=_MIGRATED_AT, in_legacy_roster=False
        )

        await _run(db)

        assert await _on_roster(db, fixture, user_id)
        assert await _holds_member_role(db, fixture, user_id)

    async def test_running_twice_changes_nothing(
        self, db: ExtendedAsyncSAEngine, fixture: _Fixture
    ) -> None:
        restored = await _add_user(db, fixture, edge_at=_MIGRATED_AT, granted_at=_MIGRATED_AT)
        kept = await _add_user(db, fixture, edge_at=_RUNTIME_AT, granted_at=_RUNTIME_AT)

        await _run(db)
        await _run(db)

        assert not await _on_roster(db, fixture, restored)
        assert await _on_roster(db, fixture, kept)
        assert await _holds_member_role(db, fixture, kept)
