"""Runs the seed-role sync against a real database and reads the rows back.

Static analysis does not reach the migration's SQL, so what it writes is checked here:
a database shaped like one seeded before the declaration goes in, the migration runs,
and what comes out is held against the fixture the declaration renders.
"""

from __future__ import annotations

import json
import pathlib
import uuid
from collections.abc import AsyncGenerator
from typing import Any

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
    downgrade,
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


_REPOSITORY = pathlib.Path(__file__).resolve().parents[5]


def _seed_files() -> tuple[dict[str, Any], dict[str, Any]]:
    base = _REPOSITORY / "fixtures" / "manager"
    accounts = json.loads((base / "example-users.json").read_text(encoding="utf-8"))
    roles = json.loads((base / "example-roles.json").read_text(encoding="utf-8"))
    return accounts, roles


@pytest.fixture
async def seeded_from_fixture(db: ExtendedAsyncSAEngine) -> dict[str, Any]:
    """The seed's own subjects and roles, put back the way a database held them before
    the declaration: no preset link, the permission rows the data migrations left, and
    none of the assignments a scope hands out on its own."""
    accounts, seed = _seed_files()
    domain = accounts["domains"][0]
    auto_ids = {role["id"] for role in seed["roles"] if role["auto_assign"]}
    async with db.begin_session() as session:
        session.add(
            DomainRow(
                id=uuid.UUID(domain["id"]),
                name=domain["name"],
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
        for group in accounts["groups"]:
            session.add(
                ProjectRow(
                    id=uuid.UUID(group["id"]),
                    name=group["name"],
                    domain_name=domain["name"],
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    dotfiles=b"",
                    type=ProjectType.GENERAL,
                    resource_policy="default",
                )
            )
        for user in accounts["users"]:
            session.add(
                UserRow(
                    uuid=uuid.UUID(user["uuid"]),
                    username=user["username"],
                    email=user["email"],
                    password=PasswordInfo(
                        password="test-password",
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=1_000,
                        salt_size=32,
                    ),
                    need_password_change=False,
                    domain_id=uuid.UUID(domain["id"]),
                    domain_name=domain["name"],
                    resource_policy="default",
                )
            )
        await session.flush()
        for row in accounts["association_groups_users"]:
            await session.execute(
                sa.insert(association_groups_users).values(
                    user_id=uuid.UUID(row["user_id"]), group_id=uuid.UUID(row["group_id"])
                )
            )
        for entity in accounts["virtual_entities"]:
            session.add(
                VirtualEntityRow(
                    id=uuid.UUID(entity["id"]),
                    entity_type=entity["entity_type"],
                    entity_id=uuid.UUID(entity["entity_id"]),
                )
            )
        for preset in seed["role_presets"]:
            session.add(
                RolePresetRow(
                    id=uuid.UUID(preset["id"]),
                    name=f"preset_{preset['name']}",
                    scope_type=preset["scope_type"],
                    auto_assign=preset["auto_assign"],
                    deleted=True,
                )
            )
        for role in seed["roles"]:
            session.add(
                RoleRow(
                    id=uuid.UUID(role["id"]),
                    name=role["name"],
                    source=RoleSource(role["source"]),
                    status=RoleStatus.ACTIVE,
                    auto_assign=role["auto_assign"],
                    scope_type=role["scope_type"],
                    scope_id=uuid.UUID(role["scope_id"]),
                )
            )
        await session.flush()
        # What the data migrations left behind, on a role of each kind.
        for role in seed["roles"][:2]:
            for entity_type in ("model_deployment", "keypair", "session:app"):
                session.add(
                    PermissionRow(
                        role_id=uuid.UUID(role["id"]),
                        entity_type=entity_type,
                        permission=1,
                        all_fields=True,
                    )
                )
        for row in seed["user_roles"]:
            if row["role_id"] in auto_ids:
                continue
            session.add(
                UserRoleRow(user_id=uuid.UUID(row["user_id"]), role_id=uuid.UUID(row["role_id"]))
            )
    by_role_id = {role["id"]: role for role in seed["roles"]}
    return {
        "expected_permissions": {
            (by_role_id[row["role_id"]]["name"], row["entity_type"], row["permission"])
            for row in seed["permissions"]
        },
        "expected_assignments": {
            (row["user_id"], by_role_id[row["role_id"]]["name"]) for row in seed["user_roles"]
        },
        "expected_roles": {
            (role["name"], role["scope_type"], role["role_preset_id"], role["source"])
            for role in seed["roles"]
        },
        "expected_preset_permissions": {
            (row["id"], row["role_preset_id"], row["entity_type"], row["permission"])
            for row in seed["role_permission_presets"]
        },
    }


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

    async def test_the_legacy_role_takes_its_graph_node(
        self, db: ExtendedAsyncSAEngine, seeded: dict[str, uuid.UUID]
    ) -> None:
        async with db.begin_session() as session:
            session.add(VirtualEntityRow(entity_type="role", entity_id=seeded["legacy_role"]))
        async with db.begin() as conn:
            await conn.run_sync(lambda sync_conn: _run(sync_conn))
        async with db.begin_readonly_session() as session:
            left = (
                await session.execute(
                    sa.select(sa.func.count())
                    .select_from(VirtualEntityRow)
                    .where(VirtualEntityRow.entity_id == seeded["legacy_role"])
                )
            ).scalar_one()
        assert left == 0

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


class TestMigratedMatchesTheSeed:
    """A database carried here holds what a database seeded from the fixture holds.

    The seed's own subjects and roles go in without their preset links, carrying the
    permission rows the data migrations left, and the assignments a scope hands out on
    its own taken away. What the migration then writes is held against the fixture,
    keyed by role name: a linked role keeps the id it came in with, so the rows are the
    same rows under different role ids.
    """

    @pytest.fixture
    async def carried(
        self, db: ExtendedAsyncSAEngine, seeded_from_fixture: dict[str, Any]
    ) -> dict[str, Any]:
        async with db.begin() as conn:
            await conn.run_sync(lambda sync_conn: _run(sync_conn))
        return seeded_from_fixture

    async def test_the_permissions_are_the_seed_s(
        self, db: ExtendedAsyncSAEngine, carried: dict[str, Any]
    ) -> None:
        async with db.begin_readonly_session() as session:
            rows = (
                await session.execute(
                    sa.select(RoleRow.name, PermissionRow.entity_type, PermissionRow.permission)
                    .select_from(PermissionRow)
                    .join(RoleRow, RoleRow.id == PermissionRow.role_id)
                )
            ).all()
        written = {(row.name, row.entity_type, int(row.permission)) for row in rows}
        assert written == carried["expected_permissions"]

    async def test_the_assignments_are_the_seed_s(
        self, db: ExtendedAsyncSAEngine, carried: dict[str, Any]
    ) -> None:
        async with db.begin_readonly_session() as session:
            rows = (
                await session.execute(
                    sa.select(UserRoleRow.user_id, RoleRow.name)
                    .select_from(UserRoleRow)
                    .join(RoleRow, RoleRow.id == UserRoleRow.role_id)
                )
            ).all()
        written = {(str(row.user_id), row.name) for row in rows}
        assert written == carried["expected_assignments"]

    async def test_the_roles_are_the_seed_s(
        self, db: ExtendedAsyncSAEngine, carried: dict[str, Any]
    ) -> None:
        async with db.begin_readonly_session() as session:
            rows = (await session.execute(sa.select(RoleRow))).scalars().all()
        written = {
            (row.name, str(row.scope_type), str(row.role_preset_id), row.source.value)
            for row in rows
        }
        assert written == carried["expected_roles"]

    async def test_the_preset_permissions_are_the_seed_s(
        self, db: ExtendedAsyncSAEngine, carried: dict[str, Any]
    ) -> None:
        async with db.begin_readonly_session() as session:
            rows = (await session.execute(sa.select(RolePermissionPresetRow))).scalars().all()
        written = {
            (str(row.id), str(row.role_preset_id), row.entity_type, int(row.permission))
            for row in rows
        }
        assert written == carried["expected_preset_permissions"]


class TestRepeating:
    """Running it again adds nothing. `downgrade` undoes nothing -- what it replaced is
    not recoverable -- so a cycle is the same as running it twice."""

    async def _rows(self, db: ExtendedAsyncSAEngine) -> dict[str, set[tuple[str, ...]]]:
        async with db.begin_readonly_session() as session:
            permissions = (await session.execute(sa.select(PermissionRow))).scalars().all()
            assignments = (await session.execute(sa.select(UserRoleRow))).scalars().all()
            presets = (await session.execute(sa.select(RolePermissionPresetRow))).scalars().all()
            roles = (await session.execute(sa.select(RoleRow))).scalars().all()
            memberships = (await session.execute(sa.select(EntityMembershipRow))).scalars().all()
            caps = (await session.execute(sa.select(EntityMembershipCapRow))).scalars().all()
        return {
            "permissions": {
                (str(row.id), str(row.role_id), row.entity_type, str(int(row.permission)))
                for row in permissions
            },
            "user_roles": {(str(row.user_id), str(row.role_id)) for row in assignments},
            "role_permission_presets": {
                (str(row.id), str(row.role_preset_id), row.entity_type, str(int(row.permission)))
                for row in presets
            },
            "roles": {(str(row.id), row.name, str(row.role_preset_id)) for row in roles},
            "entity_memberships": {
                (str(row.virtual_entity_id), str(row.member_entity_id)) for row in memberships
            },
            "entity_membership_caps": {
                (str(row.membership_id), str(int(row.permission))) for row in caps
            },
        }

    async def test_a_second_run_writes_nothing_new(
        self, db: ExtendedAsyncSAEngine, carried: dict[str, Any]
    ) -> None:
        before = await self._rows(db)
        async with db.begin() as conn:
            await conn.run_sync(lambda sync_conn: _run(sync_conn))
        assert await self._rows(db) == before

    async def test_a_cycle_writes_nothing_new(
        self, db: ExtendedAsyncSAEngine, carried: dict[str, Any]
    ) -> None:
        before = await self._rows(db)
        for _ in range(3):
            downgrade()
            async with db.begin() as conn:
                await conn.run_sync(lambda sync_conn: _run(sync_conn))
        assert await self._rows(db) == before

    @pytest.fixture
    async def carried(
        self, db: ExtendedAsyncSAEngine, seeded_from_fixture: dict[str, Any]
    ) -> dict[str, Any]:
        async with db.begin() as conn:
            await conn.run_sync(lambda sync_conn: _run(sync_conn))
        return seeded_from_fixture


class TestOnePresetPerScope:
    """`uq_roles_preset_scope` holds one role per preset per scope, and the two naming
    rules can both have left one behind on the same scope."""

    @pytest.fixture
    async def twins(
        self, db: ExtendedAsyncSAEngine, seeded: dict[str, uuid.UUID]
    ) -> dict[str, uuid.UUID]:
        """The same project carrying an admin role under each naming rule."""
        async with db.begin_session() as session:
            twin = RoleRow(
                name=f"project-{str(seeded['project'])[:8]}-admin",
                source=RoleSource.SYSTEM,
                status=RoleStatus.ACTIVE,
                scope_type=ProjectEntityType(),
                scope_id=seeded["project"],
            )
            session.add(twin)
            await session.flush()
            seeded["twin_role"] = twin.id
        return seeded

    async def test_only_one_of_them_is_linked(
        self, db: ExtendedAsyncSAEngine, twins: dict[str, uuid.UUID]
    ) -> None:
        async with db.begin() as conn:
            await conn.run_sync(lambda sync_conn: _run(sync_conn))
        async with db.begin_readonly_session() as session:
            rows = (
                (
                    await session.execute(
                        sa.select(RoleRow).where(RoleRow.scope_id == twins["project"])
                    )
                )
                .scalars()
                .all()
            )
        linked = [row for row in rows if row.role_preset_id is not None]
        by_preset = [row.role_preset_id for row in linked]
        assert len(by_preset) == len(set(by_preset)), "one preset took two roles of a scope"
