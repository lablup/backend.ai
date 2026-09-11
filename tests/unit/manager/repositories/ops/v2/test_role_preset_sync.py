"""RolePresetWriteOps.sync_preset_roles: a preset change reaches the roles it
instantiated — their permissions, name and auto_assign — and nothing else."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest
import sqlalchemy as sa
from sqlalchemy import Table

from ai.backend.common.data.entity.domain import DomainEntityType, DomainID, DomainName
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import RoleSource
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
]

_PROJECT_NAME = "alpha"


@dataclass
class Scene:
    """One project with a preset-derived role and a hand-made role beside it."""

    domain_name: DomainName
    project_id: uuid.UUID
    preset_id: RolePresetID
    derived_role_id: uuid.UUID
    custom_role_id: uuid.UUID
    user_id: uuid.UUID


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, _TABLES):
        yield database_connection


@pytest.fixture
def provider(db: ExtendedAsyncSAEngine) -> RolePresetOpsProvider:
    return RolePresetOpsProvider(db)


async def _bind_role(db: ExtendedAsyncSAEngine, project_id: uuid.UUID, role_id: uuid.UUID) -> None:
    """Enroll the role in the project's virtual entity, as creation does."""
    async with db.begin_session() as sess:
        scope_node = await sess.scalar(
            sa.select(VirtualEntityRow).where(VirtualEntityRow.entity_id == project_id)
        )
        assert scope_node is not None
        role_node = VirtualEntityRow(entity_type="role", entity_id=role_id)
        sess.add(role_node)
        await sess.flush()
        sess.add(
            EntityMembershipRow(
                virtual_entity_id=scope_node.id, member_entity_id=role_node.id, capped=False
            )
        )


async def _add_role(
    db: ExtendedAsyncSAEngine,
    project_id: uuid.UUID,
    name: str,
    *,
    preset_id: uuid.UUID | None,
) -> uuid.UUID:
    """A role holding vfolder READ on the project, bound to it."""
    role_id = uuid.uuid4()
    async with db.begin_session() as sess:
        sess.add(
            RoleRow(
                id=role_id,
                name=name,
                source=RoleSource.SYSTEM,
                status=RoleStatus.ACTIVE,
                role_preset_id=preset_id,
                scope_type=ProjectEntityType(),
                scope_id=project_id,
            )
        )
        await sess.flush()
        sess.add(
            PermissionRow(
                role_id=role_id,
                entity_type=VFolderEntityType(),
                permission=Permission.READ,
                all_fields=True,
            )
        )
    await _bind_role(db, project_id, role_id)
    return role_id


@pytest.fixture
async def scene(db: ExtendedAsyncSAEngine) -> Scene:
    domain_id = DomainID(uuid.uuid4())
    domain_name = DomainName(f"d-{uuid.uuid4().hex[:8]}")
    project_id = uuid.uuid4()
    user_id = uuid.uuid4()
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
        sess.add(
            ProjectRow(
                id=project_id,
                name=_PROJECT_NAME,
                domain_name=domain_name,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
                resource_policy="default",
                type=ProjectType.GENERAL,
            )
        )
        sess.add(
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
        sess.add(VirtualEntityRow(entity_type="project", entity_id=project_id))
        preset = RolePresetRow(
            name="member", scope_type=ProjectEntityType(), auto_assign=False, deleted=False
        )
        sess.add(preset)
        await sess.flush()
        preset_id = preset.id
        sess.add(
            RolePermissionPresetRow(
                role_preset_id=preset_id,
                entity_type=VFolderEntityType(),
                permission=Permission.READ,
            )
        )
    derived = await _add_role(db, project_id, "member-x", preset_id=preset_id)
    custom = await _add_role(db, project_id, "hand-made", preset_id=None)
    async with db.begin_session() as sess:
        sess.add(UserRoleRow(user_id=user_id, role_id=derived))
    return Scene(
        domain_name=domain_name,
        project_id=project_id,
        preset_id=preset_id,
        derived_role_id=derived,
        custom_role_id=custom,
        user_id=user_id,
    )


async def _set_preset_grants(
    db: ExtendedAsyncSAEngine,
    preset_id: uuid.UUID,
    grants: set[tuple[EntityType, Permission]],
) -> None:
    async with db.begin_session() as sess:
        await sess.execute(
            sa.delete(RolePermissionPresetRow).where(
                RolePermissionPresetRow.role_preset_id == preset_id
            )
        )
        for entity_type, permission in grants:
            sess.add(
                RolePermissionPresetRow(
                    role_preset_id=preset_id, entity_type=entity_type, permission=permission
                )
            )


async def _edit_preset(db: ExtendedAsyncSAEngine, preset_id: uuid.UUID, **values: object) -> None:
    async with db.begin_session() as sess:
        await sess.execute(
            sa.update(RolePresetRow).where(RolePresetRow.id == preset_id).values(**values)
        )


async def _sync(provider: RolePresetOpsProvider, preset_id: RolePresetID) -> None:
    async with provider.write_ops() as w:
        await w.sync_preset_roles(preset_id)


async def _permissions(
    db: ExtendedAsyncSAEngine, role_id: uuid.UUID
) -> set[tuple[str, Permission]]:
    async with db.begin_readonly_session() as sess:
        rows = await sess.execute(
            sa.select(PermissionRow.entity_type, PermissionRow.permission).where(
                PermissionRow.role_id == role_id
            )
        )
        return {(str(entity_type), Permission(permission)) for entity_type, permission in rows}


async def _role(db: ExtendedAsyncSAEngine, role_id: uuid.UUID) -> RoleRow:
    async with db.begin_readonly_session() as sess:
        row = await sess.get(RoleRow, role_id)
        assert row is not None
        return row


async def _grants(db: ExtendedAsyncSAEngine, role_id: uuid.UUID) -> set[uuid.UUID]:
    async with db.begin_readonly_session() as sess:
        return set(
            (
                await sess.scalars(
                    sa.select(UserRoleRow.user_id).where(UserRoleRow.role_id == role_id)
                )
            ).all()
        )


class TestSyncPresetRoles:
    async def test_added_grants_reach_the_derived_role(
        self, db: ExtendedAsyncSAEngine, provider: RolePresetOpsProvider, scene: Scene
    ) -> None:
        await _set_preset_grants(
            db,
            scene.preset_id,
            {
                (VFolderEntityType(), Permission.READ),
                (SessionEntityType(), Permission.READ),
                (SessionEntityType(), Permission.UPDATE),
            },
        )

        await _sync(provider, scene.preset_id)

        assert await _permissions(db, scene.derived_role_id) == {
            ("vfolder", Permission.READ),
            ("session", Permission.READ),
            ("session", Permission.UPDATE),
        }

    async def test_a_grant_the_preset_dropped_is_revoked(
        self, db: ExtendedAsyncSAEngine, provider: RolePresetOpsProvider, scene: Scene
    ) -> None:
        await _set_preset_grants(db, scene.preset_id, {(SessionEntityType(), Permission.READ)})

        await _sync(provider, scene.preset_id)

        assert await _permissions(db, scene.derived_role_id) == {("session", Permission.READ)}

    async def test_grants_to_users_and_the_role_row_survive(
        self, db: ExtendedAsyncSAEngine, provider: RolePresetOpsProvider, scene: Scene
    ) -> None:
        await _set_preset_grants(db, scene.preset_id, set())

        await _sync(provider, scene.preset_id)

        assert await _grants(db, scene.derived_role_id) == {scene.user_id}
        assert (await _role(db, scene.derived_role_id)).id == scene.derived_role_id

    async def test_a_role_without_a_preset_is_left_alone(
        self, db: ExtendedAsyncSAEngine, provider: RolePresetOpsProvider, scene: Scene
    ) -> None:
        await _set_preset_grants(db, scene.preset_id, set())
        await _edit_preset(db, scene.preset_id, name="renamed", auto_assign=True)

        await _sync(provider, scene.preset_id)

        custom = await _role(db, scene.custom_role_id)
        assert custom.name == "hand-made"
        assert custom.auto_assign is False
        assert await _permissions(db, scene.custom_role_id) == {("vfolder", Permission.READ)}

    async def test_name_and_auto_assign_follow_the_preset(
        self, db: ExtendedAsyncSAEngine, provider: RolePresetOpsProvider, scene: Scene
    ) -> None:
        await _edit_preset(db, scene.preset_id, name="renamed", auto_assign=True)

        await _sync(provider, scene.preset_id)

        derived = await _role(db, scene.derived_role_id)
        assert derived.name == f"renamed-{str(scene.project_id)[:8]}"
        assert derived.auto_assign is True

    async def test_a_templated_name_renders_from_the_scope_row(
        self, db: ExtendedAsyncSAEngine, provider: RolePresetOpsProvider, scene: Scene
    ) -> None:
        await _edit_preset(db, scene.preset_id, role_name_template="{{ scope.name }}-crew")

        await _sync(provider, scene.preset_id)

        assert (await _role(db, scene.derived_role_id)).name == f"{_PROJECT_NAME}-crew"

    async def test_a_changed_scope_type_leaves_the_role_as_it_is(
        self, db: ExtendedAsyncSAEngine, provider: RolePresetOpsProvider, scene: Scene
    ) -> None:
        await _set_preset_grants(db, scene.preset_id, set())
        await _edit_preset(db, scene.preset_id, scope_type=DomainEntityType(), name="renamed")

        await _sync(provider, scene.preset_id)

        derived = await _role(db, scene.derived_role_id)
        assert derived.name == "member-x"
        assert await _permissions(db, scene.derived_role_id) == {("vfolder", Permission.READ)}
