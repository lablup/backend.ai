"""A user created through the provisioning path reaches their own session in a shared
project through the role of their own scope."""

from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

import pytest
import sqlalchemy as sa
import yarl
from dateutil.tz import tzutc
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.resource_group import ResourceGroupID, ResourceGroupName
from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.data.entity.session import SessionEntityType, SessionID
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.dto.manager.session.request import (
    MatchSessionsRequest,
    RenameSessionRequest,
)
from ai.backend.common.dto.manager.session.response import GetSessionInfoResponse
from ai.backend.common.types import AccessKey, SessionTypes
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.keypair.types import KeyPairSecrets
from ai.backend.manager.data.permission.seed.loader import RoleSeedLoader
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.kernel import kernels
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.project import ProjectRow, association_groups_users
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserStatus, users
from ai.backend.manager.models.user.creators import UserCreator
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.user.provider import UserOpsProvider
from ai.backend.manager.repositories.ops.v2.user.write import FullUserCreator
from ai.backend.manager.secret.types import SecretValue
from ai.backend.testutils.fixtures import DomainFixtureData

if TYPE_CHECKING:
    from tests.component.conftest import ServerInfo

_BITS = (
    Permission.READ,
    Permission.UPDATE,
    Permission.CREATE,
    Permission.SOFT_DELETE,
    Permission.HARD_DELETE,
)


@dataclass(frozen=True)
class _Owner:
    user_id: UserID
    access_key: str
    secret_key: str


@pytest.fixture()
async def declared_user_owner_preset(db_engine: SAEngine) -> AsyncIterator[uuid.UUID]:
    """The user_owner preset and its grants as the seed declaration states them."""
    [seed] = [seed for seed in RoleSeedLoader().load() if seed.name == "user_owner"]
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(RolePresetRow.__table__).values(
                id=seed.id,
                name=seed.name,
                scope_type=str(seed.scope_type),
                auto_assign=seed.auto_assign,
                deleted=False,
            )
        )
        await conn.execute(
            sa.insert(RolePermissionPresetRow.__table__).values([
                {"role_preset_id": seed.id, "entity_type": entity_type, "permission": bit}
                for entity_type, granted in seed.permissions.items()
                for bit in _BITS
                if granted & bit
            ])
        )
    yield seed.id
    async with db_engine.begin() as conn:
        await conn.execute(
            RolePermissionPresetRow.__table__.delete().where(
                RolePermissionPresetRow.__table__.c.role_preset_id == seed.id
            )
        )
        await conn.execute(
            RolePresetRow.__table__.delete().where(RolePresetRow.__table__.c.id == seed.id)
        )


@pytest.fixture()
async def owner(
    database_engine: ExtendedAsyncSAEngine,
    db_engine: SAEngine,
    domain_fixture: DomainFixtureData,
    group_fixture: uuid.UUID,
    resource_policy_fixture: str,
    declared_user_owner_preset: uuid.UUID,
) -> AsyncIterator[_Owner]:
    """A regular user created the way every user is, and put on the shared project."""
    unique = secrets.token_hex(4)
    access_key = f"AKTEST{secrets.token_hex(7).upper()}"
    secret_key = secrets.token_hex(20)
    provider = UserOpsProvider(database_engine)
    async with provider.write_ops() as w:
        result = await w.create_user(
            FullUserCreator(
                user=UserCreator(
                    email=f"owner-{unique}@test.local",
                    username=f"owner-{unique}",
                    password=PasswordInfo(
                        password=secrets.token_urlsafe(8),
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=1_000,
                        salt_size=32,
                    ),
                    need_password_change=False,
                    domain_id=DomainID(domain_fixture.domain_id),
                    status=UserStatus.ACTIVE,
                    role=UserRole.USER,
                    resource_policy=resource_policy_fixture,
                ),
                keypair_secrets=KeyPairSecrets(
                    access_key=AccessKey(access_key),
                    secret_key=SecretValue(secret_key),
                    ssh_public_key="ssh-rsa test",
                    ssh_private_key="test-private-key",
                ),
                keypair_resource_policy=resource_policy_fixture,
            )
        )
        user_id = UserID(result.user.id)
        await w.join_projects(
            user_id, DomainID(domain_fixture.domain_id), [ProjectID(group_fixture)]
        )
    yield _Owner(user_id=user_id, access_key=access_key, secret_key=secret_key)
    async with db_engine.begin() as conn:
        personal_ids = (
            (
                await conn.execute(
                    sa.select(ProjectRow.__table__.c.id).where(
                        ProjectRow.__table__.c.creator_id == user_id
                    )
                )
            )
            .scalars()
            .all()
        )
        role_ids = (
            (
                await conn.execute(
                    sa.select(RoleRow.__table__.c.id).where(
                        RoleRow.__table__.c.scope_type == UserEntityType(),
                        RoleRow.__table__.c.scope_id == user_id,
                    )
                )
            )
            .scalars()
            .all()
        )
        await conn.execute(
            association_groups_users.delete().where(association_groups_users.c.user_id == user_id)
        )
        await conn.execute(keypairs.delete().where(keypairs.c.user == user_id))
        await conn.execute(
            EntityLabelRow.__table__.delete().where(
                EntityLabelRow.__table__.c.entity_id.in_([user_id, *personal_ids])
            )
        )
        # Roles, their permissions and assignments, and every edge go with the nodes.
        await conn.execute(
            VirtualEntityRow.__table__.delete().where(
                sa.or_(
                    sa.and_(
                        VirtualEntityRow.__table__.c.entity_type == RoleEntityType(),
                        VirtualEntityRow.__table__.c.entity_id.in_(role_ids),
                    ),
                    sa.and_(
                        VirtualEntityRow.__table__.c.entity_type == ProjectEntityType(),
                        VirtualEntityRow.__table__.c.entity_id.in_(personal_ids),
                    ),
                    sa.and_(
                        VirtualEntityRow.__table__.c.entity_type == UserEntityType(),
                        VirtualEntityRow.__table__.c.entity_id == user_id,
                    ),
                )
            )
        )
        await conn.execute(RoleRow.__table__.delete().where(RoleRow.__table__.c.id.in_(role_ids)))
        await conn.execute(
            ProjectRow.__table__.delete().where(ProjectRow.__table__.c.id.in_(personal_ids))
        )
        await conn.execute(users.delete().where(users.c.uuid == user_id))


@pytest.fixture()
async def owner_registry(
    server: ServerInfo,
    owner: _Owner,
) -> AsyncIterator[BackendAIClientRegistry]:
    registry = await BackendAIClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(access_key=owner.access_key, secret_key=owner.secret_key),
    )
    try:
        yield registry
    finally:
        await registry.close()


@pytest.fixture()
async def owned_session(
    db_engine: SAEngine,
    domain_fixture: DomainFixtureData,
    group_fixture: uuid.UUID,
    owner: _Owner,
    resource_group_name: ResourceGroupName,
    resource_group_id: ResourceGroupID,
) -> AsyncIterator[SessionID]:
    """The owner's RUNNING session in the shared project, with the graph rows creating it
    writes: the owner and the project each own and govern it."""
    unique = secrets.token_hex(4)
    session_id = SessionID(uuid.uuid4())
    session_name = f"test-owner-session-{unique}"
    now = datetime.now(tzutc())
    status_history: dict[str, Any] = {
        SessionStatus.PENDING.name: now.isoformat(),
        SessionStatus.RUNNING.name: now.isoformat(),
    }
    virtual_entities = VirtualEntityRow.__table__
    session_node = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(SessionRow.__table__).values(
                id=session_id,
                creation_id=f"cid-{unique}",
                name=session_name,
                session_type=SessionTypes.INTERACTIVE,
                cluster_size=1,
                cluster_mode="single-node",
                domain_name=domain_fixture.domain_name,
                domain_id=domain_fixture.domain_id,
                group_id=group_fixture,
                user_uuid=owner.user_id,
                access_key=owner.access_key,
                scaling_group_name=resource_group_name,
                resource_group_id=resource_group_id,
                status=SessionStatus.RUNNING,
                status_info="",
                status_history=status_history,
                created_at=now,
            )
        )
        await conn.execute(
            sa.insert(kernels).values(
                id=uuid.uuid4(),
                session_id=session_id,
                session_creation_id=f"cid-{unique}",
                session_name=session_name,
                session_type=SessionTypes.INTERACTIVE,
                cluster_role="main",
                cluster_idx=0,
                cluster_hostname="main0",
                cluster_mode="single-node",
                cluster_size=1,
                domain_name=domain_fixture.domain_name,
                group_id=group_fixture,
                user_uuid=owner.user_id,
                access_key=owner.access_key,
                scaling_group=resource_group_name,
                resource_group_id=resource_group_id,
                status=KernelStatus.RUNNING,
                status_info="",
                repl_in_port=0,
                repl_out_port=0,
                stdin_port=0,
                stdout_port=0,
                created_at=now,
            )
        )
        scope_nodes = (
            (
                await conn.execute(
                    sa.select(virtual_entities.c.id).where(
                        sa.or_(
                            sa.and_(
                                virtual_entities.c.entity_type == UserEntityType(),
                                virtual_entities.c.entity_id == owner.user_id,
                            ),
                            sa.and_(
                                virtual_entities.c.entity_type == ProjectEntityType(),
                                virtual_entities.c.entity_id == group_fixture,
                            ),
                        )
                    )
                )
            )
            .scalars()
            .all()
        )
        await conn.execute(
            sa.insert(virtual_entities).values(
                id=session_node, entity_type=SessionEntityType(), entity_id=session_id
            )
        )
        await conn.execute(
            sa.insert(EntityMembershipRow.__table__).values([
                {"virtual_entity_id": node, "member_entity_id": session_node, "capped": False}
                for node in (session_node, *scope_nodes)
            ])
        )
        await conn.execute(
            sa.insert(ScopeBindingRow.__table__).values([
                {"virtual_entity_id": session_node, "scope_entity_id": node, "permission_cap": None}
                for node in (session_node, *scope_nodes)
            ])
        )
    yield session_id
    async with db_engine.begin() as conn:
        await conn.execute(virtual_entities.delete().where(virtual_entities.c.id == session_node))
        await conn.execute(kernels.delete().where(kernels.c.session_id == session_id))
        await conn.execute(
            SessionRow.__table__.delete().where(SessionRow.__table__.c.id == session_id)
        )


class TestSessionOwnerThroughUserOwnerRole:
    async def test_owner_gets_own_session_info(
        self,
        owner_registry: BackendAIClientRegistry,
        owner: _Owner,
        owned_session: SessionID,
    ) -> None:
        result = await owner_registry.session.get_info(owned_session)
        assert isinstance(result, GetSessionInfoResponse)
        assert result.root["userId"] == str(owner.user_id)

    async def test_owner_renames_own_session(
        self,
        owner_registry: BackendAIClientRegistry,
        owned_session: SessionID,
    ) -> None:
        new_name = f"renamed-{secrets.token_hex(4)}"
        await owner_registry.session.rename(
            owned_session, RenameSessionRequest(session_name=new_name)
        )
        matched = await owner_registry.session.match_sessions(MatchSessionsRequest(id=new_name))
        assert [str(x["id"]) for x in matched.matches] == [str(owned_session)]
