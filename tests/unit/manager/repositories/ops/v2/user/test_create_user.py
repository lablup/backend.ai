"""Integration tests for what ``create_user`` provisions."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa
from sqlalchemy import Table

from ai.backend.common.data.entity.domain import DomainEntityType, DomainID, DomainName
from ai.backend.common.data.entity.project import (
    PROJECT_SCOPE_TYPE,
    ProjectEntityType,
    ProjectID,
)
from ai.backend.common.data.entity.role import RoleEntityType, RoleID
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.entity.virtual_entity import VirtualEntityID
from ai.backend.common.data.permission.types import RoleStatus
from ai.backend.common.types import AccessKey, ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.keypair.types import KeyPairSecrets
from ai.backend.manager.data.permission.types import EntityType, OperationType, ScopeType
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project import ProjectRow, ProjectType
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
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
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.user.creators import UserCreator
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
from ai.backend.manager.repositories.ops.v2.user.provider import UserOpsProvider
from ai.backend.manager.repositories.ops.v2.user.write import FullUserCreator
from ai.backend.manager.secret.types import SecretValue
from ai.backend.testutils.db import HasTable, with_tables
from ai.backend.testutils.fixtures import DomainFixtureData

_TABLES: list[Table | type[HasTable]] = [
    DomainRow,
    UserResourcePolicyRow,
    ProjectResourcePolicyRow,
    KeyPairResourcePolicyRow,
    RolePresetRow,
    RolePermissionPresetRow,
    RoleRow,
    PermissionRow,
    UserRoleRow,
    UserRow,
    KeyPairRow,
    ProjectRow,
    AssociationScopesEntitiesRow,
    VirtualEntityRow,
    ScopeBindingRow,
    EntityLabelRow,
    EntityMembershipRow,
    EntityMembershipCapRow,
    EntityMembershipFieldRow,
]

_KEYPAIR_POLICY_DEFAULTS = {
    "total_resource_slots": ResourceSlot(),
    "max_session_lifetime": 0,
    "max_concurrent_sessions": 30,
    "max_pending_session_count": None,
    "max_pending_session_resource_slots": None,
    "max_concurrent_sftp_sessions": 10,
    "max_containers_per_session": 1,
    "idle_timeout": 1800,
    "allowed_vfolder_hosts": VFolderHostPermissionMap(),
}


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, _TABLES):
        yield database_connection


@pytest.fixture
def provider(db: ExtendedAsyncSAEngine) -> UserOpsProvider:
    return UserOpsProvider(db)


@pytest.fixture
async def domain(db: ExtendedAsyncSAEngine) -> DomainFixtureData:
    """A domain, with the ``default`` policies every provisioned row falls back to."""
    domain_id = DomainID(uuid.uuid4())
    domain_name = DomainName(f"test-domain-{uuid.uuid4().hex[:8]}")
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
            UserResourcePolicyRow(
                name="default",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
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
        session.add(KeyPairResourcePolicyRow(name="default", **_KEYPAIR_POLICY_DEFAULTS))
        await session.commit()
    return DomainFixtureData(domain_name=domain_name, domain_id=domain_id)


async def _create_user(
    provider: UserOpsProvider,
    domain_id: DomainID,
    username: str,
    project_ids: list[ProjectID] | None = None,
) -> UserID:
    unique = uuid.uuid4().hex[:8]
    creator = UserCreator(
        email=f"{unique}@test.local",
        username=username,
        password=PasswordInfo(
            password="test-password",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=1_000,
            salt_size=32,
        ),
        need_password_change=False,
        domain_id=domain_id,
    )
    async with provider.write_ops() as w:
        result = await w.create_user(
            FullUserCreator(
                user=creator,
                keypair_secrets=KeyPairSecrets(
                    access_key=AccessKey(f"AK{unique}"),
                    secret_key=SecretValue(f"SK{unique}"),
                    ssh_public_key="ssh-rsa test",
                    ssh_private_key="test-private-key",
                ),
                keypair_resource_policy="default",
            )
        )
        user_id = UserID(result.user.id)
        await w.join_projects(user_id, domain_id, project_ids or [])
    return user_id


async def _personal_projects(
    db: ExtendedAsyncSAEngine, domain_name: DomainName
) -> list[ProjectRow]:
    async with db.begin_readonly_session() as session:
        return list(
            (
                await session.scalars(
                    sa.select(ProjectRow).where(
                        ProjectRow.domain_name == domain_name,
                        ProjectRow.type == ProjectType.PERSONAL,
                    )
                )
            ).all()
        )


def _node_of(entity_type: str, entity_id: uuid.UUID) -> sa.ScalarSelect[VirtualEntityID]:
    return (
        sa.select(VirtualEntityRow.id)
        .where(
            VirtualEntityRow.entity_type == entity_type,
            VirtualEntityRow.entity_id == entity_id,
        )
        .scalar_subquery()
    )


async def _project_member_ids(db: ExtendedAsyncSAEngine, project_id: ProjectID) -> list[str]:
    """The users enrolled in the project's virtual entity; the project's own
    self-membership is not one of them."""
    async with db.begin_readonly_session() as session:
        return [
            str(entity_id)
            for entity_id in (
                await session.scalars(
                    sa.select(VirtualEntityRow.entity_id)
                    .join(
                        EntityMembershipRow,
                        EntityMembershipRow.member_entity_id == VirtualEntityRow.id,
                    )
                    .where(
                        EntityMembershipRow.virtual_entity_id
                        == _node_of(ProjectEntityType(), project_id),
                        VirtualEntityRow.entity_type == UserEntityType(),
                    )
                )
            ).all()
        ]


class TestPersonalProjectProvisioning:
    """Creating a user creates the personal project it alone belongs to."""

    async def test_creates_one_personal_project_with_the_user_as_only_member(
        self,
        db: ExtendedAsyncSAEngine,
        provider: UserOpsProvider,
        domain: DomainFixtureData,
    ) -> None:
        user_id = await _create_user(provider, domain.domain_id, "alice")

        projects = await _personal_projects(db, domain.domain_name)
        assert len(projects) == 1
        assert projects[0].name == "alice"
        assert projects[0].resource_policy == "default"
        assert projects[0].total_resource_slots == ResourceSlot()
        assert await _project_member_ids(db, ProjectID(projects[0].id)) == [str(user_id)]

    async def test_each_user_gets_its_own_personal_project(
        self,
        db: ExtendedAsyncSAEngine,
        provider: UserOpsProvider,
        domain: DomainFixtureData,
    ) -> None:
        first = await _create_user(provider, domain.domain_id, "alice")
        second = await _create_user(provider, domain.domain_id, "bob")

        projects = {p.name: p for p in await _personal_projects(db, domain.domain_name)}
        assert set(projects) == {"alice", "bob"}
        assert await _project_member_ids(db, ProjectID(projects["alice"].id)) == [str(first)]
        assert await _project_member_ids(db, ProjectID(projects["bob"].id)) == [str(second)]

    async def test_username_is_slugified_into_the_project_name(
        self,
        db: ExtendedAsyncSAEngine,
        provider: UserOpsProvider,
        domain: DomainFixtureData,
    ) -> None:
        """A username is not a slug — signup fills it with the e-mail address."""
        await _create_user(provider, domain.domain_id, "alice@test.local")

        assert [p.name for p in await _personal_projects(db, domain.domain_name)] == [
            "alice-test.local"
        ]

    async def test_a_taken_name_gets_a_numeric_suffix(
        self,
        db: ExtendedAsyncSAEngine,
        provider: UserOpsProvider,
        domain: DomainFixtureData,
    ) -> None:
        """Two usernames slugifying to the same base still both get a project."""
        await _create_user(provider, domain.domain_id, "alice.test")
        await _create_user(provider, domain.domain_id, "alice@test")
        await _create_user(provider, domain.domain_id, "alice test")

        projects = await _personal_projects(db, domain.domain_name)
        assert sorted(p.name for p in projects) == ["alice-test", "alice-test-2", "alice.test"]

    async def test_the_personal_project_is_created_in_the_domain(
        self,
        db: ExtendedAsyncSAEngine,
        provider: UserOpsProvider,
        domain: DomainFixtureData,
    ) -> None:
        """``created_in`` puts the project on the domain's list, the way a project
        created through the project path is."""
        await _create_user(provider, domain.domain_id, "alice")
        project_id = (await _personal_projects(db, domain.domain_name))[0].id

        async with db.begin_readonly_session() as session:
            owned = await session.scalar(
                sa.select(sa.func.count())
                .select_from(EntityMembershipRow)
                .where(
                    EntityMembershipRow.virtual_entity_id
                    == _node_of(DomainEntityType(), domain.domain_id),
                    EntityMembershipRow.member_entity_id
                    == _node_of(ProjectEntityType(), project_id),
                )
            )
        assert owned == 1

    async def test_a_named_personal_project_enrolls_nobody(
        self,
        db: ExtendedAsyncSAEngine,
        provider: UserOpsProvider,
        domain: DomainFixtureData,
    ) -> None:
        """``project_ids`` naming someone else's personal project adds no member."""
        owner = await _create_user(provider, domain.domain_id, "alice")
        owned_project = ProjectID((await _personal_projects(db, domain.domain_name))[0].id)

        await _create_user(provider, domain.domain_id, "bob", project_ids=[owned_project])

        assert await _project_member_ids(db, owned_project) == [str(owner)]


async def _owns(
    db: ExtendedAsyncSAEngine,
    owner: tuple[str, uuid.UUID],
    member: tuple[str, uuid.UUID],
) -> bool:
    """Whether the owner's virtual entity lists the member, uncapped."""
    async with db.begin_readonly_session() as session:
        return bool(
            await session.scalar(
                sa.select(
                    sa.exists().where(
                        EntityMembershipRow.virtual_entity_id == _node_of(*owner),
                        EntityMembershipRow.member_entity_id == _node_of(*member),
                        EntityMembershipRow.capped.is_(False),
                    )
                )
            )
        )


async def _governs(
    db: ExtendedAsyncSAEngine,
    scope: tuple[str, uuid.UUID],
    entity: tuple[str, uuid.UUID],
) -> bool:
    """Whether the scope rules the entity's virtual entity."""
    async with db.begin_readonly_session() as session:
        return bool(
            await session.scalar(
                sa.select(
                    sa.exists().where(
                        ScopeBindingRow.virtual_entity_id == _node_of(*entity),
                        ScopeBindingRow.scope_entity_id == _node_of(*scope),
                    )
                )
            )
        )


@pytest.fixture
async def user_role_preset(db: ExtendedAsyncSAEngine) -> uuid.UUID:
    """An active user-scope preset every created user's scope instantiates."""
    preset_id = uuid.uuid4()
    async with db.begin_session() as session:
        session.add(
            RolePresetRow(
                id=preset_id,
                name="preset-user",
                scope_type=ScopeType.USER,
                auto_assign=True,
                deleted=False,
            )
        )
        await session.flush()
        session.add(
            RolePermissionPresetRow(
                role_preset_id=preset_id,
                entity_type=EntityType.VFOLDER,
                operation=OperationType.READ,
            )
        )
        await session.commit()
    return preset_id


class TestUserGraphProvisioning:
    """Creating a user puts it in the graph under its domain, with its own role."""

    async def test_the_domain_owns_and_governs_the_user(
        self,
        db: ExtendedAsyncSAEngine,
        provider: UserOpsProvider,
        domain: DomainFixtureData,
    ) -> None:
        """``created_in`` puts the user on the domain's list and under its roles."""
        user_id = await _create_user(provider, domain.domain_id, "alice")

        domain_node = (DomainEntityType(), domain.domain_id)
        user_node = (UserEntityType(), user_id)
        assert await _owns(db, domain_node, user_node)
        assert await _governs(db, domain_node, user_node)

    async def test_no_legacy_scope_association_is_written(
        self,
        db: ExtendedAsyncSAEngine,
        provider: UserOpsProvider,
        domain: DomainFixtureData,
    ) -> None:
        """Placement is the graph's answer alone; the legacy association table is
        left untouched."""
        user_id = await _create_user(provider, domain.domain_id, "alice")

        async with db.begin_readonly_session() as session:
            associations = await session.scalar(
                sa.select(sa.func.count())
                .select_from(AssociationScopesEntitiesRow)
                .where(
                    AssociationScopesEntitiesRow.entity_type == EntityType.USER,
                    AssociationScopesEntitiesRow.entity_id == str(user_id),
                )
            )
        assert associations == 0

    async def test_the_user_holds_the_roles_its_scope_presets_call_for(
        self,
        db: ExtendedAsyncSAEngine,
        provider: UserOpsProvider,
        domain: DomainFixtureData,
        user_role_preset: uuid.UUID,
    ) -> None:
        """A user scope's roles come from its presets, and the user holds the
        auto_assign ones."""
        user_id = await _create_user(provider, domain.domain_id, "alice")

        async with db.begin_readonly_session() as session:
            role = (
                await session.scalars(
                    sa.select(RoleRow)
                    .join(UserRoleRow, UserRoleRow.role_id == RoleRow.id)
                    .where(UserRoleRow.user_id == user_id)
                )
            ).one()
            entity_types = set(
                (
                    await session.scalars(
                        sa.select(PermissionRow.entity_type).where(
                            PermissionRow.role_id == role.id,
                            PermissionRow.scope_type == ScopeType.USER,
                            PermissionRow.scope_id == str(user_id),
                        )
                    )
                ).all()
            )
        assert role.name == f"preset-user-{str(user_id)[:8]}"
        assert {str(EntityType.VFOLDER)} == {str(entity_type) for entity_type in entity_types}


async def _create_project(db: ExtendedAsyncSAEngine, domain_name: DomainName) -> ProjectID:
    """A general project in the domain, the kind a user is enrolled in and out of."""
    project_id = ProjectID(uuid.uuid4())
    async with db.begin_session() as session:
        session.add(
            ProjectRow(
                id=project_id,
                name=f"project-{uuid.uuid4().hex[:8]}",
                description="Test project",
                is_active=True,
                domain_name=domain_name,
                resource_policy="default",
                type=ProjectType.GENERAL,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
                integration_id=None,
            )
        )
        await session.commit()
    return project_id


async def _enrol_auto_assign_role(db: ExtendedAsyncSAEngine, project_id: ProjectID) -> RoleID:
    """A role the project hands to whoever joins it, on the row and enrolled in the
    project's virtual entity the way the preset-derived ones are."""
    role_id = RoleID(uuid.uuid4())
    async with db.begin_session() as session:
        session.add(
            RoleRow(
                id=role_id,
                name=f"role-{role_id.hex[:8]}",
                status=RoleStatus.ACTIVE,
                auto_assign=True,
                scope_type=PROJECT_SCOPE_TYPE,
                scope_id=project_id,
            )
        )
        role_node = VirtualEntityRow(entity_type=RoleEntityType(), entity_id=role_id)
        session.add(role_node)
        await session.flush()
        project_node_id = await session.scalar(
            sa.select(VirtualEntityRow.id).where(
                VirtualEntityRow.entity_type == PROJECT_SCOPE_TYPE,
                VirtualEntityRow.entity_id == project_id,
            )
        )
        session.add(
            EntityMembershipRow(
                virtual_entity_id=project_node_id,
                member_entity_id=role_node.id,
                capped=False,
            )
        )
        await session.commit()
    return role_id


async def _held_role_ids(db: ExtendedAsyncSAEngine, user_id: UserID) -> set[RoleID]:
    async with db.begin_readonly_session() as session:
        return set(
            (
                await session.scalars(
                    sa.select(UserRoleRow.role_id).where(UserRoleRow.user_id == user_id)
                )
            ).all()
        )


class TestProjectMembershipSync:
    """Setting the user's projects joins and leaves only what changed."""

    async def test_the_user_joins_the_named_projects(
        self,
        db: ExtendedAsyncSAEngine,
        provider: UserOpsProvider,
        domain: DomainFixtureData,
    ) -> None:
        user_id = await _create_user(provider, domain.domain_id, "alice")
        project_id = await _create_project(db, domain.domain_name)

        async with provider.write_ops() as w:
            await w.replace_user_projects(user_id, domain.domain_name, [project_id])

        assert await _project_member_ids(db, project_id) == [str(user_id)]

    async def test_a_project_dropped_from_the_set_is_left(
        self,
        db: ExtendedAsyncSAEngine,
        provider: UserOpsProvider,
        domain: DomainFixtureData,
    ) -> None:
        user_id = await _create_user(provider, domain.domain_id, "alice")
        project_id = await _create_project(db, domain.domain_name)
        async with provider.write_ops() as w:
            await w.replace_user_projects(user_id, domain.domain_name, [project_id])

        async with provider.write_ops() as w:
            await w.replace_user_projects(user_id, domain.domain_name, [])

        assert await _project_member_ids(db, project_id) == []

    async def test_the_personal_project_stands_outside_the_sync(
        self,
        db: ExtendedAsyncSAEngine,
        provider: UserOpsProvider,
        domain: DomainFixtureData,
    ) -> None:
        """An empty set leaves every project but the user's own personal one."""
        user_id = await _create_user(provider, domain.domain_id, "alice")
        personal_id = ProjectID((await _personal_projects(db, domain.domain_name))[0].id)

        async with provider.write_ops() as w:
            await w.replace_user_projects(user_id, domain.domain_name, [])

        assert await _project_member_ids(db, personal_id) == [str(user_id)]

    async def test_leaving_takes_the_projects_roles_back(
        self,
        db: ExtendedAsyncSAEngine,
        provider: UserOpsProvider,
        domain: DomainFixtureData,
    ) -> None:
        """Removal is the relation and the roles together (BEP-1076): a role may only be
        chosen from the project's own, so holding one after leaving is not a state that
        arises."""
        user_id = await _create_user(provider, domain.domain_id, "alice")
        project_id = await _create_project(db, domain.domain_name)
        async with provider.write_ops() as w:
            await w.replace_user_projects(user_id, domain.domain_name, [project_id])
        role_id = await _enrol_auto_assign_role(db, project_id)
        async with provider.write_ops() as w:
            await w.replace_user_projects(user_id, domain.domain_name, [])
            await w.replace_user_projects(user_id, domain.domain_name, [project_id])
        assert role_id in await _held_role_ids(db, user_id)

        async with provider.write_ops() as w:
            await w.replace_user_projects(user_id, domain.domain_name, [])

        assert role_id not in await _held_role_ids(db, user_id)
        assert await _project_member_ids(db, project_id) == []
