"""Integration tests for what moving a user to another domain does to its projects."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa
from sqlalchemy import Table

from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.data.entity.project import PROJECT_ENTITY_TYPE, ProjectID
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE, UserID
from ai.backend.common.data.entity.virtual_entity import VirtualEntityID
from ai.backend.common.types import AccessKey, ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.keypair.types import KeyPairSecrets
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project import ProjectRow
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
from ai.backend.manager.models.user.updaters import UserUpdater
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
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.user.provider import UserOpsProvider
from ai.backend.manager.repositories.ops.v2.user.write import FullUserCreator
from ai.backend.manager.repositories.user.db_source import UserDBSource
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.secret.types import SecretValue
from ai.backend.manager.types import OptionalState
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
def user_db_source(db: ExtendedAsyncSAEngine) -> UserDBSource:
    return UserDBSource(
        db=db,
        v2_ops_provider=V2DBOpsProvider(db),
        key_provider_pool=KeyProviderPool(providers=[], write_provider_type=KeyProviderType.PLAIN),
    )


async def _create_domain(db: ExtendedAsyncSAEngine, prefix: str) -> DomainFixtureData:
    domain_id = DomainID(uuid.uuid4())
    domain_name = DomainName(f"{prefix}-{uuid.uuid4().hex[:8]}")
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
        await session.commit()
    return DomainFixtureData(domain_name=domain_name, domain_id=domain_id)


@pytest.fixture
async def policies(db: ExtendedAsyncSAEngine) -> None:
    """The ``default`` policies every provisioned row falls back to."""
    async with db.begin_session() as session:
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


@pytest.fixture
async def origin(db: ExtendedAsyncSAEngine, policies: None) -> DomainFixtureData:
    return await _create_domain(db, "origin")


@pytest.fixture
async def destination(db: ExtendedAsyncSAEngine, policies: None) -> DomainFixtureData:
    return await _create_domain(db, "destination")


async def _create_project(db: ExtendedAsyncSAEngine, domain_name: DomainName) -> ProjectID:
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


async def _create_user(
    provider: UserOpsProvider,
    domain_id: DomainID,
    project_ids: list[ProjectID],
) -> UserID:
    unique = uuid.uuid4().hex[:8]
    async with provider.write_ops() as w:
        result = await w.create_user(
            FullUserCreator(
                user=UserCreator(
                    email=f"{unique}@test.local",
                    username=f"user-{unique}",
                    password=PasswordInfo(
                        password="test-password",
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=1_000,
                        salt_size=32,
                    ),
                    need_password_change=False,
                    domain_id=domain_id,
                ),
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
        await w.enroll_in_projects(user_id, domain_id, project_ids)
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


async def _project_member_ids(db: ExtendedAsyncSAEngine, project_id: ProjectID) -> list[str]:
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


class TestUserDomainMove:
    """A user's projects are its domain's, so moving the user leaves the ones behind."""

    async def test_moving_the_user_leaves_the_origin_domain_projects(
        self,
        db: ExtendedAsyncSAEngine,
        provider: UserOpsProvider,
        user_db_source: UserDBSource,
        origin: DomainFixtureData,
        destination: DomainFixtureData,
    ) -> None:
        project_id = await _create_project(db, origin.domain_name)
        user_id = await _create_user(provider, origin.domain_id, [project_id])
        assert await _project_member_ids(db, project_id) == [str(user_id)]

        await user_db_source.update_user_by_uuid_validated(
            UserUpdater(
                user_id=user_id,
                domain_name=OptionalState.update(destination.domain_name),
            )
        )

        assert await _project_member_ids(db, project_id) == []

    async def test_moving_the_user_carries_domain_id_over(
        self,
        db: ExtendedAsyncSAEngine,
        provider: UserOpsProvider,
        user_db_source: UserDBSource,
        origin: DomainFixtureData,
        destination: DomainFixtureData,
    ) -> None:
        """``domain_name`` is the deprecated column; ``domain_id`` must follow it."""
        user_id = await _create_user(provider, origin.domain_id, [])

        await user_db_source.update_user_by_uuid_validated(
            UserUpdater(
                user_id=user_id,
                domain_name=OptionalState.update(destination.domain_name),
            )
        )

        async with db.begin_readonly_session() as session:
            row = (
                await session.execute(
                    sa.select(UserRow.domain_name, UserRow.domain_id).where(UserRow.uuid == user_id)
                )
            ).one()
        assert row.domain_name == destination.domain_name
        assert row.domain_id == destination.domain_id
