"""Integration tests for the personal project ``create_full_user`` provisions."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa
from sqlalchemy import Table

from ai.backend.common.data.entity.domain import DOMAIN_ENTITY_TYPE, DomainID, DomainName
from ai.backend.common.data.entity.project import PROJECT_ENTITY_TYPE, ProjectID
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE, UserID
from ai.backend.common.data.entity.virtual_entity import VirtualEntityID
from ai.backend.common.types import AccessKey, ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.keypair.types import KeyPairSecrets
from ai.backend.manager.data.permission.types import EntityType, ScopeType
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
from ai.backend.manager.repositories.ops.user.provider import UserOpsProvider
from ai.backend.manager.repositories.ops.user.write import FullUserCreation
from ai.backend.manager.repositories.user.creators import UserScopeCreation
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
        result = await w.create_full_user(
            FullUserCreation(
                creation=UserScopeCreation(spec=creator),
                domain_id=domain_id,
                project_ids=project_ids or [],
                keypair_resource_policy="default",
                keypair_secrets=KeyPairSecrets(
                    access_key=AccessKey(f"AK{unique}"),
                    secret_key=SecretValue(f"SK{unique}"),
                    ssh_public_key="ssh-rsa test",
                    ssh_private_key="test-private-key",
                ),
            )
        )
    return UserID(result.user_row.uuid)


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
                        == _node_of(PROJECT_ENTITY_TYPE, project_id),
                        VirtualEntityRow.entity_type == USER_ENTITY_TYPE,
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
                    == _node_of(DOMAIN_ENTITY_TYPE, domain.domain_id),
                    EntityMembershipRow.member_entity_id
                    == _node_of(PROJECT_ENTITY_TYPE, project_id),
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

    async def test_the_user_is_associated_with_the_project_scope(
        self,
        db: ExtendedAsyncSAEngine,
        provider: UserOpsProvider,
        domain: DomainFixtureData,
    ) -> None:
        """The roster write reaches the legacy scope association too."""
        user_id = await _create_user(provider, domain.domain_id, "alice")
        project_id = (await _personal_projects(db, domain.domain_name))[0].id

        async with db.begin_readonly_session() as session:
            associated = await session.scalar(
                sa.select(sa.func.count())
                .select_from(AssociationScopesEntitiesRow)
                .where(
                    AssociationScopesEntitiesRow.scope_type == ScopeType.PROJECT,
                    AssociationScopesEntitiesRow.scope_id == str(project_id),
                    AssociationScopesEntitiesRow.entity_type == EntityType.USER,
                    AssociationScopesEntitiesRow.entity_id == str(user_id),
                )
            )
        assert associated == 1
