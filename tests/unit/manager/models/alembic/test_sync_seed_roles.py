"""Runs the seed-role sync against a real database and reads the rows back.

Static analysis does not reach the migration's SQL, so what it writes is checked here:
a database shaped like one seeded before the declaration goes in, the migration runs,
and what comes out is held against the fixture the declaration renders.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa
from sqlalchemy import Table

from ai.backend.common.data.entity.domain import DomainEntityType, DomainID, DomainName
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import RoleSource
from ai.backend.manager.models.alembic.versions.f4a1c9d20b73_sync_seed_roles_with_their_declaration import (
    _PRESETS,
    _drop_unlinked_system_roles,
    _grant_auto_assign_roles,
    _identify,
    _link_roles,
    _retire_names,
    _sweep_unknown_types,
    _write_presets,
    _write_role_permissions,
)
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.project.row import (
    ProjectRow,
    ProjectType,
    association_groups_users,
)
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
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.testutils.db import HasTable, with_tables

_TABLES: list[Table | type[HasTable]] = [
    DomainRow,
    UserResourcePolicyRow,
    ProjectResourcePolicyRow,
    KeyPairResourcePolicyRow,
    UserRow,
    ProjectRow,
    association_groups_users,
    RolePresetRow,
    RolePermissionPresetRow,
    RoleRow,
    PermissionRow,
    UserRoleRow,
    VirtualEntityRow,
    EntityMembershipRow,
    EntityMembershipCapRow,
]

_PRESET_BY_NAME = {preset.name: preset for preset in _PRESETS}


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, _TABLES):
        yield database_connection


@pytest.fixture
async def seeded(db: ExtendedAsyncSAEngine) -> dict[str, uuid.UUID]:
    """A database shaped like one seeded before the declaration: presets soft-deleted,
    roles pointing at nothing, and permission rows naming types since retired."""
    domain_id = DomainID(uuid.uuid4())
    domain_name = DomainName(f"test-domain-{uuid.uuid4().hex[:8]}")
    project_id = uuid.uuid4()
    admin_id = uuid.uuid4()
    member_id = uuid.uuid4()
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
                name="default",
                domain_name=domain_name,
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
                dotfiles=b"",
                type=ProjectType.GENERAL,
                resource_policy="default",
            )
        )
        for user_id, name in ((admin_id, "admin"), (member_id, "member")):
            session.add(
                UserRow(
                    uuid=user_id,
                    username=name,
                    email=f"{name}@example.com",
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
        await session.flush()
        for user_id in (admin_id, member_id):
            await session.execute(
                sa.insert(association_groups_users).values(user_id=user_id, group_id=project_id)
            )
        # The presets a database carries: soft-deleted, which is why nothing links.
        for preset in _PRESETS:
            session.add(
                RolePresetRow(
                    id=preset.id,
                    name=f"preset_{preset.name}",
                    scope_type=preset.scope_type,
                    auto_assign=preset.auto_assign,
                    deleted=True,
                )
            )
        roles = {
            "project_admin": RoleRow(
                name=f"role_project_{str(project_id)[:8]}_admin",
                source=RoleSource.SYSTEM,
                status=RoleStatus.ACTIVE,
                scope_type=ProjectEntityType(),
                scope_id=project_id,
            ),
            "project_member": RoleRow(
                name=f"role_project_{str(project_id)[:8]}_member",
                source=RoleSource.SYSTEM,
                status=RoleStatus.ACTIVE,
                auto_assign=True,
                scope_type=ProjectEntityType(),
                scope_id=project_id,
            ),
            "domain_admin": RoleRow(
                name=f"role_domain_{domain_name}_admin",
                source=RoleSource.SYSTEM,
                status=RoleStatus.ACTIVE,
                scope_type=DomainEntityType(),
                scope_id=domain_id,
            ),
            "legacy": RoleRow(
                name="role_superadmin",
                source=RoleSource.SYSTEM,
                status=RoleStatus.ACTIVE,
                scope_type=DomainEntityType(),
                scope_id=domain_id,
            ),
            "custom": RoleRow(
                name="a-role-someone-made",
                source=RoleSource.CUSTOM,
                status=RoleStatus.ACTIVE,
                scope_type=ProjectEntityType(),
                scope_id=project_id,
            ),
        }
        session.add_all(roles.values())
        await session.flush()
        # What the data migrations left: names since retired, on both kinds of role.
        for role in (roles["project_admin"], roles["custom"]):
            for entity_type in ("model_deployment", "keypair", "session:app", "vfolder:data"):
                session.add(
                    PermissionRow(
                        role_id=role.id, entity_type=entity_type, permission=1, all_fields=True
                    )
                )
        session.add(UserRoleRow(user_id=admin_id, role_id=roles["project_admin"].id))
        for entity_type, entity_id in (
            (DomainEntityType(), domain_id),
            (ProjectEntityType(), project_id),
            (UserEntityType(), admin_id),
            (UserEntityType(), member_id),
        ):
            session.add(VirtualEntityRow(entity_type=entity_type, entity_id=entity_id))
        return {
            "domain": domain_id,
            "project": project_id,
            "admin": admin_id,
            "member": member_id,
            "project_admin_role": roles["project_admin"].id,
            "project_member_role": roles["project_member"].id,
            "legacy_role": roles["legacy"].id,
            "custom_role": roles["custom"].id,
        }


@pytest.fixture
async def migrated(db: ExtendedAsyncSAEngine, seeded: dict[str, uuid.UUID]) -> dict[str, uuid.UUID]:
    async with db.begin() as conn:
        await conn.run_sync(lambda sync_conn: _run(sync_conn))
    return seeded


def _run(conn: sa.engine.Connection) -> None:
    """The steps `upgrade()` runs, in its order. Called directly: `op.get_bind()` reads
    a context alembic is not running here."""
    _retire_names(conn)
    _sweep_unknown_types(conn)
    _write_presets(conn)
    _link_roles(conn)
    _drop_unlinked_system_roles(conn)
    _write_role_permissions(conn)
    _grant_auto_assign_roles(conn)


class TestSyncSeedRoles:
    async def test_the_presets_come_back_live(
        self, db: ExtendedAsyncSAEngine, migrated: dict[str, uuid.UUID]
    ) -> None:
        async with db.begin_readonly_session() as session:
            rows = (await session.execute(sa.select(RolePresetRow))).scalars().all()
        assert {(row.id, row.name, row.deleted) for row in rows} == {
            (uuid.UUID(preset.id), preset.name, False) for preset in _PRESETS
        }

    async def test_the_seed_roles_name_their_preset(
        self, db: ExtendedAsyncSAEngine, migrated: dict[str, uuid.UUID]
    ) -> None:
        async with db.begin_readonly_session() as session:
            rows = (await session.execute(sa.select(RoleRow))).scalars().all()
        by_id = {uuid.UUID(str(row.id)): row for row in rows}
        assert by_id[migrated["project_admin_role"]].role_preset_id == uuid.UUID(
            _PRESET_BY_NAME["project_admin"].id
        )
        assert by_id[migrated["project_member_role"]].role_preset_id == uuid.UUID(
            _PRESET_BY_NAME["project_member"].id
        )

    async def test_the_legacy_system_role_goes_and_the_custom_one_stays(
        self, db: ExtendedAsyncSAEngine, migrated: dict[str, uuid.UUID]
    ) -> None:
        async with db.begin_readonly_session() as session:
            ids = set((await session.execute(sa.select(RoleRow.id))).scalars().all())
        assert migrated["legacy_role"] not in ids
        assert migrated["custom_role"] in ids

    async def test_the_retired_names_are_gone_from_every_role(
        self, db: ExtendedAsyncSAEngine, migrated: dict[str, uuid.UUID]
    ) -> None:
        async with db.begin_readonly_session() as session:
            named = set(
                (await session.execute(sa.select(PermissionRow.entity_type))).scalars().all()
            )
        assert not named & {"model_deployment", "keypair", "session:app", "vfolder:data"}

    async def test_a_linked_role_holds_what_its_preset_states(
        self, db: ExtendedAsyncSAEngine, migrated: dict[str, uuid.UUID]
    ) -> None:
        preset = _PRESET_BY_NAME["project_admin"]
        async with db.begin_readonly_session() as session:
            rows = (
                (
                    await session.execute(
                        sa.select(PermissionRow).where(
                            PermissionRow.role_id == migrated["project_admin_role"]
                        )
                    )
                )
                .scalars()
                .all()
            )
        written = {(row.entity_type, int(row.permission)) for row in rows}
        stated = {(entity_type, bit) for entity_type, bits in preset.grants for bit in bits}
        assert written == stated

    async def test_the_ids_are_the_ones_the_seed_derives(
        self, db: ExtendedAsyncSAEngine, migrated: dict[str, uuid.UUID]
    ) -> None:
        role_id = migrated["project_admin_role"]
        async with db.begin_readonly_session() as session:
            rows = (
                (
                    await session.execute(
                        sa.select(PermissionRow).where(PermissionRow.role_id == role_id)
                    )
                )
                .scalars()
                .all()
            )
        for row in rows:
            assert str(row.id) == _identify(
                "permission", str(role_id), row.entity_type, str(int(row.permission))
            )

    async def test_every_project_member_holds_the_auto_assign_role(
        self, db: ExtendedAsyncSAEngine, migrated: dict[str, uuid.UUID]
    ) -> None:
        async with db.begin_readonly_session() as session:
            holders = set(
                (
                    await session.execute(
                        sa.select(UserRoleRow.user_id).where(
                            UserRoleRow.role_id == migrated["project_member_role"]
                        )
                    )
                )
                .scalars()
                .all()
            )
        assert holders == {migrated["admin"], migrated["member"]}

    async def test_the_roster_edge_carries_a_read_cap(
        self, db: ExtendedAsyncSAEngine, migrated: dict[str, uuid.UUID]
    ) -> None:
        async with db.begin_readonly_session() as session:
            scope = (
                await session.execute(
                    sa.select(VirtualEntityRow.id).where(
                        VirtualEntityRow.entity_id == migrated["project"]
                    )
                )
            ).scalar_one()
            member = (
                await session.execute(
                    sa.select(VirtualEntityRow.id).where(
                        VirtualEntityRow.entity_id == migrated["member"]
                    )
                )
            ).scalar_one()
            membership = (
                await session.execute(
                    sa.select(EntityMembershipRow).where(
                        EntityMembershipRow.virtual_entity_id == scope,
                        EntityMembershipRow.member_entity_id == member,
                    )
                )
            ).scalar_one()
            caps = (
                (
                    await session.execute(
                        sa.select(EntityMembershipCapRow).where(
                            EntityMembershipCapRow.membership_id == membership.id
                        )
                    )
                )
                .scalars()
                .all()
            )
        assert membership.capped is True
        assert [(int(cap.permission), cap.all_fields) for cap in caps] == [(1, True)]

    async def test_running_it_twice_changes_nothing(
        self, db: ExtendedAsyncSAEngine, migrated: dict[str, uuid.UUID]
    ) -> None:
        async def snapshot() -> set[tuple[str, str, int]]:
            async with db.begin_readonly_session() as session:
                rows = (await session.execute(sa.select(PermissionRow))).scalars().all()
            return {(str(row.id), row.entity_type, int(row.permission)) for row in rows}

        before = await snapshot()
        async with db.begin() as conn:
            await conn.run_sync(lambda sync_conn: _run(sync_conn))
        assert await snapshot() == before
