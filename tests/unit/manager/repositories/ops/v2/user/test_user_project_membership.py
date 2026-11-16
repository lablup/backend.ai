"""Integration tests for the projects a user is put on and taken off."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa
from sqlalchemy import Table

from ai.backend.common.data.entity.domain import DomainEntityType, DomainID, DomainName
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.entity.virtual_entity import VirtualEntityID
from ai.backend.common.types import AccessKey, ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.keypair.types import KeyPairSecrets
from ai.backend.manager.errors.resource import ModelStoreProjectLeaveError
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project import ProjectRow, ProjectType
from ai.backend.manager.models.project.creators import ProjectCreator
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
    global_entity_ids: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(global_entity_ids, _TABLES):
        yield global_entity_ids


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
        await session.flush()
        node = VirtualEntityRow(entity_type=DomainEntityType(), entity_id=domain_id)
        session.add(node)
        await session.flush()
        session.add(
            EntityMembershipRow(virtual_entity_id=node.id, member_entity_id=node.id, capped=False)
        )
        session.add(
            ScopeBindingRow(virtual_entity_id=node.id, scope_entity_id=node.id, permission_cap=None)
        )
        await session.commit()
    return DomainFixtureData(domain_name=domain_name, domain_id=domain_id)


async def _create_project(
    provider: UserOpsProvider,
    domain: DomainFixtureData,
    name: str,
    project_type: ProjectType,
) -> ProjectID:
    async with provider.write_ops() as w:
        project = await w.create_role_managed_entity(
            ProjectCreator(
                name=name,
                domain_id=domain.domain_id,
                domain_name=domain.domain_name,
                type=project_type,
                resource_policy="default",
            )
        )
    return ProjectID(project.id)


@pytest.fixture
async def model_store(provider: UserOpsProvider, domain: DomainFixtureData) -> ProjectID:
    return await _create_project(provider, domain, "model-store", ProjectType.MODEL_STORE)


@pytest.fixture
async def general(provider: UserOpsProvider, domain: DomainFixtureData) -> ProjectID:
    return await _create_project(provider, domain, "general", ProjectType.GENERAL)


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


def _node_of(entity_type: str, entity_id: uuid.UUID) -> sa.ScalarSelect[VirtualEntityID]:
    return (
        sa.select(VirtualEntityRow.id)
        .where(
            VirtualEntityRow.entity_type == entity_type,
            VirtualEntityRow.entity_id == entity_id,
        )
        .scalar_subquery()
    )


async def _joined_project_ids(db: ExtendedAsyncSAEngine, user_id: UserID) -> set[uuid.UUID]:
    """The non-personal projects whose roster lists the user."""
    async with db.begin_readonly_session() as session:
        return {
            entity_id
            for entity_id in (
                await session.scalars(
                    sa.select(VirtualEntityRow.entity_id)
                    .join(
                        EntityMembershipRow,
                        EntityMembershipRow.virtual_entity_id == VirtualEntityRow.id,
                    )
                    .where(
                        EntityMembershipRow.member_entity_id == _node_of(UserEntityType(), user_id),
                        VirtualEntityRow.entity_type == ProjectEntityType(),
                        VirtualEntityRow.entity_id.not_in(
                            sa.select(ProjectRow.id).where(ProjectRow.type == ProjectType.PERSONAL)
                        ),
                    )
                )
            ).all()
        }


class TestJoiningProjects:
    """Creating a user puts it on the domain's model-store roster."""

    async def test_the_model_store_project_is_joined_without_being_named(
        self,
        db: ExtendedAsyncSAEngine,
        provider: UserOpsProvider,
        domain: DomainFixtureData,
        model_store: ProjectID,
    ) -> None:
        user_id = await _create_user(provider, domain.domain_id, "alice")

        assert await _joined_project_ids(db, user_id) == {model_store}

    async def test_a_named_project_is_joined_alongside_it(
        self,
        db: ExtendedAsyncSAEngine,
        provider: UserOpsProvider,
        domain: DomainFixtureData,
        model_store: ProjectID,
        general: ProjectID,
    ) -> None:
        user_id = await _create_user(provider, domain.domain_id, "alice", [general])

        assert await _joined_project_ids(db, user_id) == {model_store, general}


class TestReplacingProjects:
    """Updating a user states its projects again; a model-store one cannot be dropped."""

    async def test_a_request_dropping_the_model_store_project_is_refused(
        self,
        provider: UserOpsProvider,
        domain: DomainFixtureData,
        model_store: ProjectID,
        general: ProjectID,
    ) -> None:
        user_id = await _create_user(provider, domain.domain_id, "alice", [general])

        with pytest.raises(ModelStoreProjectLeaveError):
            async with provider.write_ops() as w:
                await w.replace_user_projects(user_id, domain.domain_name, [general])

    async def test_a_request_naming_it_replaces_the_rest(
        self,
        db: ExtendedAsyncSAEngine,
        provider: UserOpsProvider,
        domain: DomainFixtureData,
        model_store: ProjectID,
        general: ProjectID,
    ) -> None:
        other = await _create_project(provider, domain, "other", ProjectType.GENERAL)
        user_id = await _create_user(provider, domain.domain_id, "alice", [general])

        async with provider.write_ops() as w:
            await w.replace_user_projects(user_id, domain.domain_name, [model_store, other])

        assert await _joined_project_ids(db, user_id) == {model_store, other}

    async def test_a_domain_without_a_model_store_project_replaces_freely(
        self,
        db: ExtendedAsyncSAEngine,
        provider: UserOpsProvider,
        domain: DomainFixtureData,
        general: ProjectID,
    ) -> None:
        """Nothing is dropped that a model-store project holds, so nothing is refused."""
        user_id = await _create_user(provider, domain.domain_id, "alice", [general])

        async with provider.write_ops() as w:
            await w.replace_user_projects(user_id, domain.domain_name, [])

        assert await _joined_project_ids(db, user_id) == set()

    async def test_the_users_own_personal_project_is_never_left(
        self,
        db: ExtendedAsyncSAEngine,
        provider: UserOpsProvider,
        domain: DomainFixtureData,
        model_store: ProjectID,
        general: ProjectID,
    ) -> None:
        user_id = await _create_user(provider, domain.domain_id, "alice", [general])

        async with provider.write_ops() as w:
            await w.replace_user_projects(user_id, domain.domain_name, [model_store])

        async with db.begin_readonly_session() as session:
            personal_id = await session.scalar(
                sa.select(ProjectRow.id).where(
                    ProjectRow.domain_name == domain.domain_name,
                    ProjectRow.type == ProjectType.PERSONAL,
                )
            )
            assert personal_id is not None
            still_a_member = await session.scalar(
                sa.select(
                    sa.exists().where(
                        EntityMembershipRow.virtual_entity_id
                        == _node_of(ProjectEntityType(), personal_id),
                        EntityMembershipRow.member_entity_id == _node_of(UserEntityType(), user_id),
                    )
                )
            )
        assert still_a_member


class TestLeavingARoster:
    """The refusal is on the roster primitive, so no path writes around it."""

    async def test_the_roster_refuses_to_take_a_user_off_the_model_store_project(
        self,
        provider: UserOpsProvider,
        domain: DomainFixtureData,
        model_store: ProjectID,
    ) -> None:
        user_id = await _create_user(provider, domain.domain_id, "alice")

        with pytest.raises(ModelStoreProjectLeaveError):
            async with provider.write_ops() as w:
                await w.leave_member(model_store, user_id)

    async def test_the_roster_takes_a_user_off_a_general_project(
        self,
        db: ExtendedAsyncSAEngine,
        provider: UserOpsProvider,
        domain: DomainFixtureData,
        model_store: ProjectID,
        general: ProjectID,
    ) -> None:
        user_id = await _create_user(provider, domain.domain_id, "alice", [general])

        async with provider.write_ops() as w:
            await w.leave_member(general, user_id)

        assert await _joined_project_ids(db, user_id) == {model_store}
