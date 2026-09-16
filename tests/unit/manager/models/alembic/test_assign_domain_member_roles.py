"""Runs the domain_member backfill against a real database and reads the rows back."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest
import sqlalchemy as sa
from sqlalchemy import Table

from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.data.permission.types import Permission, RoleStatus
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.permission.types import RoleSource
from ai.backend.manager.models.alembic.versions.e7d2a9c41b60_assign_every_user_their_domain_member_role import (
    _PRESET_ID,
    backfill,
    mark_auto_assign,
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

_PRESET_UUID = uuid.UUID(_PRESET_ID)
_GRANTS = {(str(ResourceGroupEntityType()), Permission.READ)}
_DOMAIN_ENTITY_TYPE = "domain"


@dataclass
class _Fixture:
    plain_domain: DomainID
    domain_with_role: DomainID
    domain_without_node: DomainID
    plain_user: uuid.UUID
    user_of_domain_with_role: uuid.UUID
    user_without_node: uuid.UUID
    existing_role: uuid.UUID


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


def _domain(domain_id: DomainID, name: DomainName) -> DomainRow:
    return DomainRow(
        id=domain_id,
        name=name,
        description="",
        is_active=True,
        total_resource_slots=ResourceSlot(),
        allowed_vfolder_hosts=VFolderHostPermissionMap(),
        allowed_docker_registries=[],
        dotfiles=b"",
        integration_id=None,
    )


def _user(user_id: uuid.UUID, index: int, domain_id: DomainID, domain_name: DomainName) -> UserRow:
    return UserRow(
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


@pytest.fixture
async def seeded(db: ExtendedAsyncSAEngine) -> _Fixture:
    """A database carrying no domain_member preset, and one domain per state: a plain
    one, one already holding a role nobody was assigned, and one with no graph node."""
    domain_ids = [DomainID(uuid.uuid4()) for _ in range(3)]
    domain_names = [DomainName(f"test-domain-{uuid.uuid4().hex[:8]}") for _ in range(3)]
    user_ids = [uuid.uuid4() for _ in range(3)]
    existing_role = uuid.uuid4()
    async with db.begin_session() as session:
        session.add(
            UserResourcePolicyRow(
                name="default",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=1,
                max_customized_image_count=0,
            )
        )
        for domain_id, name in zip(domain_ids, domain_names, strict=True):
            session.add(_domain(domain_id, name))
        await session.flush()
        for index, (user_id, domain_id, name) in enumerate(
            zip(user_ids, domain_ids, domain_names, strict=True)
        ):
            session.add(_user(user_id, index, domain_id, name))
        # The third domain is left out of the graph.
        for domain_id in domain_ids[:2]:
            await _node(session, _DOMAIN_ENTITY_TYPE, uuid.UUID(str(domain_id)))
        session.add(
            RoleRow(
                id=existing_role,
                name=f"domain_member-{str(domain_ids[1])[:8]}",
                source=RoleSource.SYSTEM,
                status=RoleStatus.ACTIVE,
                auto_assign=False,
                role_preset_id=None,
                scope_type=_DOMAIN_ENTITY_TYPE,
                scope_id=uuid.UUID(str(domain_ids[1])),
            )
        )
        await session.commit()
    return _Fixture(
        plain_domain=domain_ids[0],
        domain_with_role=domain_ids[1],
        domain_without_node=domain_ids[2],
        plain_user=user_ids[0],
        user_of_domain_with_role=user_ids[1],
        user_without_node=user_ids[2],
        existing_role=existing_role,
    )


async def _run_backfill(db: ExtendedAsyncSAEngine) -> None:
    async with db.begin() as conn:
        await conn.run_sync(backfill)


async def _preset_roles_of(db: ExtendedAsyncSAEngine, domain_id: DomainID) -> list[RoleRow]:
    async with db.begin_readonly_session() as session:
        return list(
            (
                await session.scalars(
                    sa.select(RoleRow).where(
                        RoleRow.scope_type == _DOMAIN_ENTITY_TYPE,
                        RoleRow.scope_id == uuid.UUID(str(domain_id)),
                        RoleRow.role_preset_id == _PRESET_UUID,
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


class TestAssignDomainMemberRoles:
    async def test_the_preset_is_written_and_assigned_on_its_own(
        self, db: ExtendedAsyncSAEngine, seeded: _Fixture
    ) -> None:
        await _run_backfill(db)

        async with db.begin_readonly_session() as session:
            preset = await session.get(RolePresetRow, _PRESET_UUID)
            grants = set(
                (
                    await session.execute(
                        sa.select(
                            RolePermissionPresetRow.entity_type,
                            RolePermissionPresetRow.permission,
                        ).where(RolePermissionPresetRow.role_preset_id == _PRESET_UUID)
                    )
                ).all()
            )
        assert preset is not None
        assert preset.name == "domain_member"
        assert preset.scope_type == _DOMAIN_ENTITY_TYPE
        assert preset.auto_assign is True
        assert preset.deleted is False
        assert {(str(entity_type), permission) for entity_type, permission in grants} == _GRANTS

    async def test_a_domain_gets_the_role_and_its_users_hold_it(
        self, db: ExtendedAsyncSAEngine, seeded: _Fixture
    ) -> None:
        await _run_backfill(db)

        [role] = await _preset_roles_of(db, seeded.plain_domain)
        assert role.name == f"domain_member-{str(seeded.plain_domain)[:8]}"
        assert role.source == RoleSource.SYSTEM
        assert role.status == RoleStatus.ACTIVE
        assert role.auto_assign is True
        assert await _grants(db, role.id) == _GRANTS
        assert await _held(db, seeded.plain_user) == [role.id]

    async def test_the_created_role_is_owned_and_governed_by_the_domain_scope(
        self, db: ExtendedAsyncSAEngine, seeded: _Fixture
    ) -> None:
        await _run_backfill(db)

        [role] = await _preset_roles_of(db, seeded.plain_domain)
        role_node = await _node_id(db, RoleEntityType(), role.id)
        domain_node = await _node_id(db, _DOMAIN_ENTITY_TYPE, uuid.UUID(str(seeded.plain_domain)))
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
        assert edges == {(role_node, False), (domain_node, False)}
        assert bindings == {role_node, domain_node}

    async def test_a_role_of_another_preset_does_not_stand_in(
        self, db: ExtendedAsyncSAEngine, seeded: _Fixture
    ) -> None:
        """The domain already holds a role by that name that no preset made, so the
        preset is instantiated beside it rather than skipped."""
        await _run_backfill(db)

        [role] = await _preset_roles_of(db, seeded.domain_with_role)
        assert role.id != seeded.existing_role
        assert await _held(db, seeded.user_of_domain_with_role) == [role.id]

    async def test_a_domain_without_a_node_is_left_out(
        self, db: ExtendedAsyncSAEngine, seeded: _Fixture
    ) -> None:
        await _run_backfill(db)

        assert await _preset_roles_of(db, seeded.domain_without_node) == []
        assert await _held(db, seeded.user_without_node) == []

    async def test_running_again_changes_nothing(
        self, db: ExtendedAsyncSAEngine, seeded: _Fixture
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

    async def test_downgrade_keeps_what_users_hold(
        self, db: ExtendedAsyncSAEngine, seeded: _Fixture
    ) -> None:
        await _run_backfill(db)
        [role] = await _preset_roles_of(db, seeded.plain_domain)

        async with db.begin() as conn:
            await conn.run_sync(lambda sync_conn: mark_auto_assign(sync_conn, False))

        async with db.begin_readonly_session() as session:
            preset = await session.get(RolePresetRow, _PRESET_UUID)
            kept = await session.get(RoleRow, role.id)
        assert preset is not None
        assert preset.auto_assign is False
        assert kept is not None
        assert kept.auto_assign is False
        assert await _held(db, seeded.plain_user) == [role.id]
