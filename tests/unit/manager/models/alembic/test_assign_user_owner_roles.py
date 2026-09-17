"""Runs the user_owner backfill against a real database and reads the rows back."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest
import sqlalchemy as sa
from sqlalchemy import Table

from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.data.permission.types import Permission, RoleStatus
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.permission.types import RoleSource
from ai.backend.manager.models.alembic.versions.dc61fa027fc1_assign_every_user_their_user_owner_role import (
    _USER_OWNER_PRESET_ID,
    backfill,
)
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
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
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.testutils.db import HasTable, with_tables

_TABLES: list[Table | type[HasTable]] = [
    DomainRow,
    UserResourcePolicyRow,
    ProjectResourcePolicyRow,
    KeyPairResourcePolicyRow,
    UserRow,
    RolePresetRow,
    RolePermissionPresetRow,
    RoleRow,
    PermissionRow,
    UserRoleRow,
    VirtualEntityRow,
    EntityMembershipRow,
    ScopeBindingRow,
]

_PRESET_ID = uuid.UUID(_USER_OWNER_PRESET_ID)
_GRANTS = {
    (str(SessionEntityType()), Permission.READ),
    (str(SessionEntityType()), Permission.HARD_DELETE),
    (str(VFolderEntityType()), Permission.READ),
}


@dataclass
class _Users:
    without_role: uuid.UUID
    unassigned: uuid.UUID
    assigned: uuid.UUID
    without_node: uuid.UUID
    unassigned_role: uuid.UUID
    assigned_role: uuid.UUID


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, _TABLES):
        yield database_connection


async def _node(
    session: sa.ext.asyncio.AsyncSession, entity_type: str, entity_id: uuid.UUID
) -> None:
    await session.execute(
        sa.insert(VirtualEntityRow.__table__).values(entity_type=entity_type, entity_id=entity_id)
    )


@pytest.fixture
async def users(db: ExtendedAsyncSAEngine) -> _Users:
    """The user_owner preset as the earlier revision left it, and one user per state:
    no role, a role nobody was assigned, a role already assigned, and no graph node."""
    domain_id = DomainID(uuid.uuid4())
    domain_name = DomainName(f"test-domain-{uuid.uuid4().hex[:8]}")
    ids = [uuid.uuid4() for _ in range(4)]
    role_ids = [uuid.uuid4(), uuid.uuid4()]
    async with db.begin_session() as session:
        session.add(
            DomainRow(
                id=domain_id,
                name=domain_name,
                description="",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
                allowed_docker_registries=[],
                dotfiles=b"",
                integration_id=None,
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
        for index, user_id in enumerate(ids):
            session.add(
                UserRow(
                    uuid=user_id,
                    username=f"user-{index}",
                    email=f"user-{index}@example.com",
                    password=PasswordInfo(
                        password="test-password",
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=1_000,
                        salt_size=32,
                    ),
                    need_password_change=False,
                    domain_id=domain_id,
                    domain_name=domain_name,
                    resource_policy="default",
                )
            )
        session.add(
            RolePresetRow(
                id=_PRESET_ID,
                name="user_owner",
                scope_type=UserEntityType(),
                auto_assign=False,
                deleted=False,
            )
        )
        await session.flush()
        for entity_type, permission in _GRANTS:
            session.add(
                RolePermissionPresetRow(
                    role_preset_id=_PRESET_ID, entity_type=entity_type, permission=permission
                )
            )
        for user_id in ids[:3]:
            await _node(session, UserEntityType(), user_id)
        for role_id, user_id in zip(role_ids, ids[1:3], strict=True):
            session.add(
                RoleRow(
                    id=role_id,
                    name=f"role_user_{user_id.hex[:8]}",
                    source=RoleSource.SYSTEM,
                    status=RoleStatus.ACTIVE,
                    auto_assign=False,
                    role_preset_id=_PRESET_ID,
                    scope_type=UserEntityType(),
                    scope_id=user_id,
                )
            )
            await session.flush()
            await _node(session, RoleEntityType(), role_id)
            session.add(
                PermissionRow(
                    role_id=role_id,
                    entity_type=SessionEntityType(),
                    permission=Permission.READ,
                )
            )
        session.add(UserRoleRow(user_id=ids[2], role_id=role_ids[1]))
        await session.commit()
    return _Users(
        without_role=ids[0],
        unassigned=ids[1],
        assigned=ids[2],
        without_node=ids[3],
        unassigned_role=role_ids[0],
        assigned_role=role_ids[1],
    )


async def _run_backfill(db: ExtendedAsyncSAEngine) -> None:
    async with db.begin() as conn:
        await conn.run_sync(backfill)


async def _roles_of(db: ExtendedAsyncSAEngine, user_id: uuid.UUID) -> list[RoleRow]:
    async with db.begin_readonly_session() as session:
        return list(
            (
                await session.scalars(
                    sa.select(RoleRow).where(
                        RoleRow.scope_type == UserEntityType(), RoleRow.scope_id == user_id
                    )
                )
            ).all()
        )


async def _held(db: ExtendedAsyncSAEngine, user_id: uuid.UUID) -> list[uuid.UUID]:
    async with db.begin_readonly_session() as session:
        return list(
            (
                await session.scalars(
                    sa.select(UserRoleRow.role_id).where(UserRoleRow.user_id == user_id)
                )
            ).all()
        )


async def _grants(db: ExtendedAsyncSAEngine, role_id: uuid.UUID) -> set[tuple[str, Permission]]:
    async with db.begin_readonly_session() as session:
        rows = (
            await session.execute(
                sa.select(PermissionRow.entity_type, PermissionRow.permission).where(
                    PermissionRow.role_id == role_id
                )
            )
        ).all()
    return {(str(entity_type), permission) for entity_type, permission in rows}


async def _node_id(
    db: ExtendedAsyncSAEngine, entity_type: str, entity_id: uuid.UUID
) -> uuid.UUID | None:
    async with db.begin_readonly_session() as session:
        node_id = await session.scalar(
            sa.select(VirtualEntityRow.id).where(
                VirtualEntityRow.entity_type == entity_type,
                VirtualEntityRow.entity_id == entity_id,
            )
        )
    return None if node_id is None else uuid.UUID(str(node_id))


class TestAssignUserOwnerRoles:
    async def test_the_preset_is_assigned_on_its_own(
        self, db: ExtendedAsyncSAEngine, users: _Users
    ) -> None:
        await _run_backfill(db)

        async with db.begin_readonly_session() as session:
            preset = await session.get(RolePresetRow, _PRESET_ID)
        assert preset is not None
        assert preset.auto_assign is True

    async def test_a_user_without_a_role_gets_one_from_the_preset(
        self, db: ExtendedAsyncSAEngine, users: _Users
    ) -> None:
        await _run_backfill(db)

        [role] = await _roles_of(db, users.without_role)
        assert role.name == f"user_owner-{str(users.without_role)[:8]}"
        assert role.role_preset_id == _PRESET_ID
        assert role.source == RoleSource.SYSTEM
        assert role.status == RoleStatus.ACTIVE
        assert role.auto_assign is True
        assert await _held(db, users.without_role) == [role.id]
        assert await _grants(db, role.id) == _GRANTS

    async def test_the_created_role_is_owned_and_governed_by_the_user_scope(
        self, db: ExtendedAsyncSAEngine, users: _Users
    ) -> None:
        await _run_backfill(db)

        [role] = await _roles_of(db, users.without_role)
        role_node = await _node_id(db, RoleEntityType(), role.id)
        user_node = await _node_id(db, UserEntityType(), users.without_role)
        assert role_node is not None
        async with db.begin_readonly_session() as session:
            edges = set(
                (
                    await session.execute(
                        sa.select(
                            EntityMembershipRow.virtual_entity_id, EntityMembershipRow.capped
                        ).where(EntityMembershipRow.member_entity_id == role_node)
                    )
                ).all()
            )
            bindings = set(
                (
                    await session.scalars(
                        sa.select(ScopeBindingRow.scope_entity_id).where(
                            ScopeBindingRow.virtual_entity_id == role_node
                        )
                    )
                ).all()
            )
        assert edges == {(role_node, False), (user_node, False)}
        assert bindings == {role_node, user_node}

    async def test_an_existing_role_is_assigned_and_kept(
        self, db: ExtendedAsyncSAEngine, users: _Users
    ) -> None:
        await _run_backfill(db)

        [role] = await _roles_of(db, users.unassigned)
        assert role.id == users.unassigned_role
        assert role.auto_assign is True
        assert await _held(db, users.unassigned) == [users.unassigned_role]
        assert await _grants(db, role.id) == {(str(SessionEntityType()), Permission.READ)}

    async def test_an_assigned_user_is_left_as_is(
        self, db: ExtendedAsyncSAEngine, users: _Users
    ) -> None:
        await _run_backfill(db)

        assert [role.id for role in await _roles_of(db, users.assigned)] == [users.assigned_role]
        assert await _held(db, users.assigned) == [users.assigned_role]

    async def test_a_user_without_a_node_is_left_out(
        self, db: ExtendedAsyncSAEngine, users: _Users
    ) -> None:
        await _run_backfill(db)

        assert await _roles_of(db, users.without_node) == []
        assert await _held(db, users.without_node) == []

    async def test_running_again_changes_nothing(
        self, db: ExtendedAsyncSAEngine, users: _Users
    ) -> None:
        await _run_backfill(db)
        async with db.begin_readonly_session() as session:
            before = [
                await session.scalar(sa.select(sa.func.count()).select_from(table))
                for table in (RoleRow, PermissionRow, UserRoleRow, VirtualEntityRow)
            ]

        await _run_backfill(db)

        async with db.begin_readonly_session() as session:
            after = [
                await session.scalar(sa.select(sa.func.count()).select_from(table))
                for table in (RoleRow, PermissionRow, UserRoleRow, VirtualEntityRow)
            ]
        assert after == before
