"""RolePresetWriteOps.provision_preset_roles: every domain, project, user and global entity in
the graph gets the role of each active preset it lacks, and the roles its scope hands out on
its own. A preset pointed at one scope gets its role there alone."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Mapping
from dataclasses import dataclass

import pytest
import sqlalchemy as sa
from sqlalchemy import Table

from ai.backend.common.data.entity.domain import DomainEntityType, DomainID, DomainName
from ai.backend.common.data.entity.global_entity import GlobalEntityID, GlobalEntityName
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, GlobalEntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import RoleSource
from ai.backend.manager.errors.role_preset import RolePresetScopeNotFound
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project import ProjectRow, ProjectType
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.permission_field import PermissionFieldRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.role_preset.provider import RolePresetOpsProvider
from ai.backend.testutils.db import HasTable, with_tables

_TABLES: list[Table | type[HasTable]] = [
    DomainRow,
    UserResourcePolicyRow,
    ProjectResourcePolicyRow,
    KeyPairResourcePolicyRow,
    UserRow,
    KeyPairRow,
    ProjectRow,
    RolePresetRow,
    RolePermissionPresetRow,
    RoleRow,
    PermissionRow,
    PermissionFieldRow,
    UserRoleRow,
    VirtualEntityRow,
    EntityMembershipRow,
    EntityMembershipCapRow,
    ScopeBindingRow,
]

# (name, scope type, auto_assign, deleted)
_PRESETS: list[tuple[str, EntityType, bool, bool]] = [
    ("domain_admin", DomainEntityType(), False, False),
    ("project_admin", ProjectEntityType(), False, False),
    ("project_member", ProjectEntityType(), True, False),
    ("user_owner", UserEntityType(), True, False),
    ("public_member", GlobalEntityType(), True, False),
    ("retired", ProjectEntityType(), False, True),
]


@dataclass
class Scene:
    """A domain with two projects and three users. Alice made the first project and
    is on its roster with Bob; Carol made the second and is on no roster."""

    domain_id: uuid.UUID
    project_id: uuid.UUID
    other_project_id: uuid.UUID
    users: dict[str, uuid.UUID]
    presets: dict[str, RolePresetID]


@pytest.fixture
async def db(
    global_entity_ids: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(global_entity_ids, _TABLES):
        yield global_entity_ids


@pytest.fixture
async def scene(db: ExtendedAsyncSAEngine) -> Scene:
    domain_id = DomainID(uuid.uuid4())
    domain_name = DomainName(f"d-{uuid.uuid4().hex[:8]}")
    project_id = uuid.uuid4()
    other_project_id = uuid.uuid4()
    users = {name: uuid.uuid4() for name in ("alice", "bob", "carol")}
    async with db.begin_session() as sess:
        sess.add(
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
        sess.add(
            ProjectResourcePolicyRow(
                name="default", max_vfolder_count=0, max_quota_scope_size=-1, max_network_count=3
            )
        )
        sess.add(
            UserResourcePolicyRow(
                name="default",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
        )
        await sess.flush()
        for name, user_id in users.items():
            sess.add(
                UserRow(
                    uuid=user_id,
                    username=name,
                    email=f"{name}-{uuid.uuid4().hex[:8]}@test.local",
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
        await sess.flush()
        for pid, name, creator in (
            (project_id, "alpha", users["alice"]),
            (other_project_id, "beta", users["carol"]),
        ):
            sess.add(
                ProjectRow(
                    id=pid,
                    name=name,
                    domain_name=domain_name,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    resource_policy="default",
                    type=ProjectType.GENERAL,
                    creator_id=UserID(creator),
                )
            )
        nodes: dict[uuid.UUID, VirtualEntityRow] = {}
        for entity_type, entity_id in (
            (DomainEntityType(), domain_id),
            (ProjectEntityType(), project_id),
            (ProjectEntityType(), other_project_id),
            *((UserEntityType(), user_id) for user_id in users.values()),
        ):
            nodes[entity_id] = VirtualEntityRow(entity_type=entity_type, entity_id=entity_id)
            sess.add(nodes[entity_id])
        rows = {
            name: RolePresetRow(
                name=name, scope_type=scope_type, auto_assign=auto_assign, deleted=deleted
            )
            for name, scope_type, auto_assign, deleted in _PRESETS
        }
        sess.add_all(rows.values())
        await sess.flush()
        presets = {name: row.id for name, row in rows.items()}
        sess.add(
            RolePermissionPresetRow(
                role_preset_id=presets["project_member"],
                entity_type=VFolderEntityType(),
                permission=Permission.READ,
            )
        )
        for name in ("alice", "bob"):
            sess.add(
                EntityMembershipRow(
                    virtual_entity_id=nodes[project_id].id,
                    member_entity_id=nodes[users[name]].id,
                    capped=True,
                )
            )
    return Scene(
        domain_id=domain_id,
        project_id=project_id,
        other_project_id=other_project_id,
        users=users,
        presets=presets,
    )


def _preset_scopes(scene: Scene) -> dict[RolePresetID, EntityIdentifier]:
    return {scene.presets["public_member"]: global_entity_id(GlobalEntityName.PUBLIC)}


async def _provision(
    db: ExtendedAsyncSAEngine,
    scene: Scene,
    preset_scopes: Mapping[RolePresetID, EntityIdentifier] | None = None,
) -> None:
    async with RolePresetOpsProvider(db).write_ops() as w:
        await w.provision_preset_roles(
            [scene.presets["project_admin"]],
            _preset_scopes(scene) if preset_scopes is None else preset_scopes,
        )


async def _role(db: ExtendedAsyncSAEngine, preset_id: uuid.UUID, scope_id: uuid.UUID) -> RoleRow:
    async with db.begin_readonly_session() as sess:
        row = await sess.scalar(
            sa.select(RoleRow).where(
                RoleRow.role_preset_id == preset_id, RoleRow.scope_id == scope_id
            )
        )
        assert row is not None
        return row


async def _holders(db: ExtendedAsyncSAEngine, role_id: uuid.UUID) -> set[uuid.UUID]:
    async with db.begin_readonly_session() as sess:
        return set(
            (
                await sess.scalars(
                    sa.select(UserRoleRow.user_id).where(UserRoleRow.role_id == role_id)
                )
            ).all()
        )


@pytest.fixture
async def provisioned(db: ExtendedAsyncSAEngine, scene: Scene) -> Scene:
    await _provision(db, scene)
    return scene


class TestProvisionPresetRoles:
    async def test_every_scope_gets_the_role_of_each_active_preset(
        self, db: ExtendedAsyncSAEngine, provisioned: Scene
    ) -> None:
        async with db.begin_readonly_session() as sess:
            rows = (await sess.execute(sa.select(RoleRow.role_preset_id, RoleRow.scope_id))).all()
        names = {preset_id: name for name, preset_id in provisioned.presets.items()}
        users = provisioned.users
        assert {(names[preset_id], scope_id) for preset_id, scope_id in rows} == {
            ("domain_admin", provisioned.domain_id),
            ("project_admin", provisioned.project_id),
            ("project_member", provisioned.project_id),
            ("project_admin", provisioned.other_project_id),
            ("project_member", provisioned.other_project_id),
            ("user_owner", users["alice"]),
            ("user_owner", users["bob"]),
            ("user_owner", users["carol"]),
            ("public_member", global_entity_id(GlobalEntityName.PUBLIC)),
        }

    async def test_a_created_role_is_owned_by_its_scope(
        self, db: ExtendedAsyncSAEngine, provisioned: Scene
    ) -> None:
        role = await _role(db, provisioned.presets["project_member"], provisioned.project_id)
        async with db.begin_readonly_session() as sess:
            node = await sess.scalar(
                sa.select(VirtualEntityRow.id).where(
                    VirtualEntityRow.entity_type == "role", VirtualEntityRow.entity_id == role.id
                )
            )
            scope = await sess.scalar(
                sa.select(VirtualEntityRow.id).where(
                    VirtualEntityRow.entity_id == provisioned.project_id
                )
            )
            owned = await sess.scalar(
                sa.select(sa.func.count())
                .select_from(EntityMembershipRow)
                .where(
                    EntityMembershipRow.virtual_entity_id == scope,
                    EntityMembershipRow.member_entity_id == node,
                )
            )
        assert node is not None
        assert owned == 1

    async def test_a_created_role_holds_what_its_preset_states(
        self, db: ExtendedAsyncSAEngine, provisioned: Scene
    ) -> None:
        role = await _role(db, provisioned.presets["project_member"], provisioned.project_id)
        async with db.begin_readonly_session() as sess:
            rows = (
                await sess.execute(
                    sa.select(PermissionRow.entity_type, PermissionRow.permission).where(
                        PermissionRow.role_id == role.id
                    )
                )
            ).all()
        assert {(str(entity_type), Permission(bit)) for entity_type, bit in rows} == {
            (str(VFolderEntityType()), Permission.READ)
        }

    async def test_a_user_holds_their_own_role(
        self, db: ExtendedAsyncSAEngine, provisioned: Scene
    ) -> None:
        for user_id in provisioned.users.values():
            role = await _role(db, provisioned.presets["user_owner"], user_id)
            assert await _holders(db, role.id) == {user_id}

    async def test_every_user_holds_the_public_role(
        self, db: ExtendedAsyncSAEngine, provisioned: Scene
    ) -> None:
        role = await _role(
            db, provisioned.presets["public_member"], global_entity_id(GlobalEntityName.PUBLIC)
        )
        assert await _holders(db, role.id) == set(provisioned.users.values())

    async def test_a_roster_member_holds_the_project_s_auto_assign_role(
        self, db: ExtendedAsyncSAEngine, provisioned: Scene
    ) -> None:
        role = await _role(db, provisioned.presets["project_member"], provisioned.project_id)
        users = provisioned.users
        assert await _holders(db, role.id) == {users["alice"], users["bob"]}

    async def test_a_creator_on_the_roster_holds_the_admin_role(
        self, db: ExtendedAsyncSAEngine, provisioned: Scene
    ) -> None:
        role = await _role(db, provisioned.presets["project_admin"], provisioned.project_id)
        assert await _holders(db, role.id) == {provisioned.users["alice"]}

    async def test_a_creator_off_the_roster_does_not(
        self, db: ExtendedAsyncSAEngine, provisioned: Scene
    ) -> None:
        role = await _role(db, provisioned.presets["project_admin"], provisioned.other_project_id)
        assert await _holders(db, role.id) == set()

    async def test_running_it_again_changes_nothing(
        self, db: ExtendedAsyncSAEngine, provisioned: Scene
    ) -> None:
        async def snapshot() -> tuple[set[tuple[str, ...]], set[tuple[str, ...]], int]:
            async with db.begin_readonly_session() as sess:
                roles = (await sess.execute(sa.select(RoleRow.id, RoleRow.role_preset_id))).all()
                grants = (
                    await sess.execute(sa.select(UserRoleRow.user_id, UserRoleRow.role_id))
                ).all()
                edges = await sess.scalar(
                    sa.select(sa.func.count()).select_from(EntityMembershipRow)
                )
            return (
                {(str(role_id), str(preset_id)) for role_id, preset_id in roles},
                {(str(user_id), str(role_id)) for user_id, role_id in grants},
                edges or 0,
            )

        before = await snapshot()
        await _provision(db, provisioned)
        assert await snapshot() == before


class TestAScopedPreset:
    """A preset pointed at one scope has its role there alone."""

    async def test_the_preset_records_its_scope(
        self, db: ExtendedAsyncSAEngine, provisioned: Scene
    ) -> None:
        async with db.begin_readonly_session() as sess:
            scope_id = await sess.scalar(
                sa.select(RolePresetRow.scope_id).where(
                    RolePresetRow.id == provisioned.presets["public_member"]
                )
            )
        assert scope_id == global_entity_id(GlobalEntityName.PUBLIC)

    async def test_no_other_scope_of_its_type_gets_the_role(
        self, db: ExtendedAsyncSAEngine, provisioned: Scene
    ) -> None:
        async with db.begin_readonly_session() as sess:
            scope_ids = (
                await sess.scalars(
                    sa.select(RoleRow.scope_id).where(
                        RoleRow.role_preset_id == provisioned.presets["public_member"]
                    )
                )
            ).all()
        assert scope_ids == [global_entity_id(GlobalEntityName.PUBLIC)]

    async def test_the_role_holds_what_its_preset_states(
        self, db: ExtendedAsyncSAEngine, scene: Scene
    ) -> None:
        async with db.begin_session() as sess:
            sess.add(
                RolePermissionPresetRow(
                    role_preset_id=scene.presets["public_member"],
                    entity_type=VFolderEntityType(),
                    permission=Permission.READ,
                )
            )
        await _provision(db, scene)
        role = await _role(
            db, scene.presets["public_member"], global_entity_id(GlobalEntityName.PUBLIC)
        )
        async with db.begin_readonly_session() as sess:
            rows = (
                await sess.execute(
                    sa.select(PermissionRow.entity_type, PermissionRow.permission).where(
                        PermissionRow.role_id == role.id
                    )
                )
            ).all()
        assert {(str(entity_type), Permission(bit)) for entity_type, bit in rows} == {
            (str(VFolderEntityType()), Permission.READ)
        }

    async def test_a_scope_without_a_virtual_entity_is_refused(
        self, db: ExtendedAsyncSAEngine, scene: Scene
    ) -> None:
        with pytest.raises(RolePresetScopeNotFound):
            await _provision(
                db, scene, {scene.presets["public_member"]: GlobalEntityID(uuid.uuid4())}
            )


class TestAHeldPresetRole:
    """A scope already holding a preset's role keeps that role."""

    @pytest.fixture
    async def held(self, db: ExtendedAsyncSAEngine, scene: Scene) -> uuid.UUID:
        role_id = uuid.uuid4()
        async with db.begin_session() as sess:
            sess.add(
                RoleRow(
                    id=role_id,
                    name="kept",
                    source=RoleSource.SYSTEM,
                    status=RoleStatus.ACTIVE,
                    auto_assign=True,
                    role_preset_id=scene.presets["project_member"],
                    scope_type=ProjectEntityType(),
                    scope_id=scene.project_id,
                )
            )
        await _provision(db, scene)
        return role_id

    async def test_it_is_not_created_again(
        self, db: ExtendedAsyncSAEngine, scene: Scene, held: uuid.UUID
    ) -> None:
        role = await _role(db, scene.presets["project_member"], scene.project_id)
        assert role.id == held
