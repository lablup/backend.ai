"""Component test fixtures for project v2 endpoints.

Covers two scenarios:
1. The original `unassign_users` endpoint (admin SDK).
2. ASE-based project membership gating for `user.search_by_project`
   (BA-5821 migration), where membership is granted via either
   `project.assign_users` or `rbac.assign_role(project_id=...)`.
"""

from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
import yarl
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import (
    Concern,
    ConcernMeta,
    GroupMeta,
)
from ai.backend.manager.api.adapters.project.adapter import ProjectAdapter
from ai.backend.manager.api.adapters.rbac.adapter import RBACAdapter
from ai.backend.manager.api.adapters.user.adapter import UserAdapter
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.project.handler import V2ProjectHandler
from ai.backend.manager.api.rest.v2.project.registry import register_v2_project_routes
from ai.backend.manager.api.rest.v2.rbac.handler import V2RBACHandler
from ai.backend.manager.api.rest.v2.rbac.registry import register_v2_rbac_routes
from ai.backend.manager.api.rest.v2.user.handler import V2UserHandler
from ai.backend.manager.api.rest.v2.user.registry import register_v2_user_routes
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import (
    EntityType,
    Permission,
    ScopeType,
)
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.dependencies.infrastructure.redis import ValkeyClients
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.user import users
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.domain.repository import DomainRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.relation.provider import RelationOpsProvider
from ai.backend.manager.repositories.ops.v2.roster.provider import RosterOpsProvider
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.manager.repositories.project.repositories import ProjectRepositories
from ai.backend.manager.repositories.project.repository import ProjectRepository
from ai.backend.manager.repositories.rbac.relation_repository import RbacRelationRepository
from ai.backend.manager.repositories.rbac.roster_repository import RbacRosterRepository
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.secret.types import SecretValue
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.domain.service import DomainService
from ai.backend.manager.services.permission_contoller.processors import (
    PermissionControllerProcessors,
)
from ai.backend.manager.services.permission_contoller.service import PermissionControllerService
from ai.backend.manager.services.processors import Processors
from ai.backend.manager.services.project.processors import ProjectProcessors
from ai.backend.manager.services.project.service import ProjectService
from ai.backend.manager.services.rbac.processors import RbacProcessors
from ai.backend.manager.services.rbac.service import (
    RbacRelationService,
    RbacRoleService,
    RbacRosterService,
)
from ai.backend.manager.services.user.processors import UserProcessors
from ai.backend.manager.services.user.service import UserService
from ai.backend.testutils.fixtures import DomainFixtureData

if TYPE_CHECKING:
    from tests.component.conftest import ServerInfo, UserFixtureData, VirtualEntitySeeder


# ---------------------------------------------------------------------------
# Processor fixtures (real DB, real RBAC enforcement)
# ---------------------------------------------------------------------------


@pytest.fixture()
def group_processors(
    database_engine: ExtendedAsyncSAEngine,
    storage_manager: AsyncMock,
    config_provider: ManagerConfigProvider,
    valkey_clients: ValkeyClients,
    processor_registry: ProcessorRegistry[Any],
) -> ProjectProcessors:
    """Real DB-backed ProjectProcessors with real RBAC validators."""
    repo = ProjectRepository(
        database_engine,
        V2DBOpsProvider(database_engine),
        config_provider,
        valkey_clients.stat,
        storage_manager,
    )
    repositories = ProjectRepositories(repository=repo)
    service = ProjectService(
        storage_manager=storage_manager,
        config_provider=config_provider,
        valkey_stat_client=valkey_clients.stat,
        group_repositories=repositories,
    )
    return ProjectProcessors(processor_registry.group(GroupMeta(ProjectEntityType())), service)


@pytest.fixture()
def user_processors(
    database_engine: ExtendedAsyncSAEngine,
    agent_registry: AgentRegistry,
    valkey_clients: ValkeyClients,
    config_provider: ManagerConfigProvider,
    processor_registry: ProcessorRegistry[Any],
) -> UserProcessors:
    """Real UserProcessors for user.search_by_project SDK calls."""
    repo = UserRepository(
        database_engine,
        V2DBOpsProvider(database_engine),
        ShareOpsProvider(database_engine),
        KeyProviderPool(providers=[], write_provider_type=KeyProviderType.PLAIN),
    )
    service = UserService(
        storage_manager=AsyncMock(),
        valkey_stat_client=valkey_clients.stat,
        agent_registry=agent_registry,
        user_repository=repo,
        scheduling_controller=AsyncMock(),
    )
    return UserProcessors(
        processor_registry.group(GroupMeta(UserEntityType())),
        service,
    )


@pytest.fixture()
def permission_controller_processors(
    database_engine: ExtendedAsyncSAEngine,
    processor_registry: ProcessorRegistry[Any],
    valkey_clients: ValkeyClients,
    config_provider: ManagerConfigProvider,
) -> PermissionControllerProcessors:
    """Real PermissionControllerProcessors for rbac.assign_role / revoke_role SDK calls."""
    perm_repo = PermissionControllerRepository(database_engine)
    service = PermissionControllerService(
        perm_repo,
        rbac_action_registry=[],
    )
    return PermissionControllerProcessors(
        processor_registry.group(GroupMeta(RoleEntityType())),
        service=service,
        action_monitors=[],
    )


@pytest.fixture()
def domain_processors(
    database_engine: ExtendedAsyncSAEngine,
    processor_registry: ProcessorRegistry[Any],
) -> DomainProcessors:
    """The adapter resolves a domain name to its id, so this runs against the DB."""
    service = DomainService(
        repository=DomainRepository(database_engine, V2DBOpsProvider(database_engine))
    )
    return DomainProcessors(processor_registry.group(GroupMeta(DomainEntityType())), service, [])


@pytest.fixture()
def rbac_processors(
    database_engine: ExtendedAsyncSAEngine,
    processor_registry: ProcessorRegistry[Any],
) -> RbacProcessors:
    """Real RbacProcessors for the project roster SDK calls."""
    rbac_groups = processor_registry.concern(ConcernMeta(Concern.RBAC))
    return RbacProcessors(
        rbac_groups.relation_group(),
        rbac_groups.group(GroupMeta(UserEntityType())),
        RbacRelationService(RbacRelationRepository(RelationOpsProvider(database_engine))),
        RbacRosterService(RbacRosterRepository(RosterOpsProvider(database_engine))),
        RbacRoleService(
            PermissionControllerRepository(database_engine),
            RbacRosterRepository(RosterOpsProvider(database_engine)),
        ),
        [],
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    config_provider: ManagerConfigProvider,
    group_processors: ProjectProcessors,
    user_processors: UserProcessors,
    domain_processors: DomainProcessors,
    permission_controller_processors: PermissionControllerProcessors,
    rbac_processors: RbacProcessors,
) -> list[RouteRegistry]:
    """Register v2 project, user, and RBAC routes for testing."""
    processors = MagicMock(spec=Processors)
    processors.project = group_processors
    processors.domain = domain_processors
    processors.user = user_processors
    processors.permission_controller = permission_controller_processors
    processors.rbac = rbac_processors

    proj_handler = V2ProjectHandler(
        adapter=ProjectAdapter(
            processors.project, processors.rbac, processors.domain, processors.user
        )
    )
    user_handler = V2UserHandler(
        adapter=UserAdapter(
            processors.user,
            processors.domain,
            config_provider.config.auth,
            KeyProviderPool(providers=[], write_provider_type=KeyProviderType.PLAIN),
        )
    )
    rbac_handler = V2RBACHandler(
        adapter=RBACAdapter(processors.rbac, processors.permission_controller)
    )

    v2_reg = RouteRegistry.create("v2", route_deps.cors_options)
    v2_reg.add_subregistry(register_v2_project_routes(proj_handler, route_deps))
    v2_reg.add_subregistry(register_v2_user_routes(user_handler, route_deps))
    v2_reg.add_subregistry(register_v2_rbac_routes(rbac_handler, route_deps))
    return [v2_reg]


# ---------------------------------------------------------------------------
# Admin-side RBAC fixture (for unassign tests)
# ---------------------------------------------------------------------------


@pytest.fixture()
async def rbac_permission_fixture(
    db_engine: SAEngine,
    admin_user_fixture: UserFixtureData,
    group_fixture: uuid.UUID,
) -> AsyncIterator[uuid.UUID]:
    """Seed minimal RBAC data so the admin user has PROJECT:UPDATE permission.

    Creates a role, assigns it to the admin user, and grants PROJECT:UPDATE
    permission scoped to the test project. Yields the role UUID and cleans up.
    """
    role_id = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(RoleRow.__table__).values(
                id=role_id,
                name=f"test-project-admin-{secrets.token_hex(4)}",
                status=RoleStatus.ACTIVE,
                scope_type=ScopeType.PROJECT.value,
                scope_id=group_fixture,
            )
        )
        await conn.execute(
            sa.insert(UserRoleRow.__table__).values(
                user_id=admin_user_fixture.user_uuid,
                role_id=role_id,
            )
        )
        await conn.execute(
            sa.insert(PermissionRow.__table__).values(
                role_id=role_id,
                entity_type=EntityType.PROJECT,
                permission=Permission.UPDATE,
            )
        )

    yield role_id

    async with db_engine.begin() as conn:
        await conn.execute(
            PermissionRow.__table__.delete().where(PermissionRow.__table__.c.role_id == role_id)
        )
        await conn.execute(
            UserRoleRow.__table__.delete().where(UserRoleRow.__table__.c.role_id == role_id)
        )
        await conn.execute(RoleRow.__table__.delete().where(RoleRow.__table__.c.id == role_id))


# ---------------------------------------------------------------------------
# Project / role fixtures (for membership-gating tests)
# ---------------------------------------------------------------------------


@pytest.fixture()
async def admin_target_project_permission(
    db_engine: SAEngine,
    admin_user_fixture: UserFixtureData,
    target_project_fixture: uuid.UUID,
) -> AsyncIterator[uuid.UUID]:
    """Grant the admin user PROJECT:UPDATE on target_project_fixture.

    Required so admin's `project.assign_users` / `project.unassign_users`
    against the target project pass the scope RBAC validator.
    """
    role_id = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(RoleRow.__table__).values(
                id=role_id,
                name=f"test-target-admin-{secrets.token_hex(4)}",
                status=RoleStatus.ACTIVE,
                scope_type=ScopeType.PROJECT.value,
                scope_id=target_project_fixture,
            )
        )
        await conn.execute(
            sa.insert(UserRoleRow.__table__).values(
                user_id=admin_user_fixture.user_uuid,
                role_id=role_id,
            )
        )
        await conn.execute(
            sa.insert(PermissionRow.__table__).values(
                role_id=role_id,
                entity_type=EntityType.PROJECT,
                permission=Permission.UPDATE,
            )
        )
    yield role_id
    async with db_engine.begin() as conn:
        await conn.execute(
            PermissionRow.__table__.delete().where(PermissionRow.__table__.c.role_id == role_id)
        )
        await conn.execute(
            UserRoleRow.__table__.delete().where(UserRoleRow.__table__.c.role_id == role_id)
        )
        await conn.execute(RoleRow.__table__.delete().where(RoleRow.__table__.c.id == role_id))


@pytest.fixture()
async def target_project_fixture(
    db_engine: SAEngine,
    domain_fixture: DomainFixtureData,
    resource_policy_fixture: str,
) -> AsyncIterator[uuid.UUID]:
    """Insert a fresh project where regular_user is NOT pre-bound.

    The shared ``regular_user_fixture`` automatically binds the user to
    ``group_fixture``; using a different project here lets `assign_users`
    actually exercise the full assignment path (including UserRoleRow
    creation) instead of being filtered out by the already-assigned check.
    """
    project_id = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(ProjectRow.__table__).values(
                id=project_id,
                name=f"target-project-{secrets.token_hex(6)}",
                description="Primary test project for membership scenarios",
                is_active=True,
                domain_name=domain_fixture.domain_name,
                resource_policy=resource_policy_fixture,
            )
        )
        virtual_entity_id = uuid.uuid4()
        await conn.execute(
            sa.insert(VirtualEntityRow.__table__).values(
                id=virtual_entity_id,
                entity_type=ScopeType.PROJECT,
                entity_id=project_id,
            )
        )
        await conn.execute(
            sa.insert(EntityMembershipRow.__table__).values(
                virtual_entity_id=virtual_entity_id,
                member_entity_id=virtual_entity_id,
                capped=False,
            )
        )
        await conn.execute(
            sa.insert(ScopeBindingRow.__table__).values(
                virtual_entity_id=virtual_entity_id,
                scope_entity_id=virtual_entity_id,
                permission_cap=None,
            )
        )
    yield project_id
    async with db_engine.begin() as conn:
        await conn.execute(
            VirtualEntityRow.__table__.delete().where(
                VirtualEntityRow.__table__.c.entity_type == ScopeType.PROJECT,
                VirtualEntityRow.__table__.c.entity_id == project_id,
            )
        )
        await conn.execute(
            ProjectRow.__table__.delete().where(ProjectRow.__table__.c.id == project_id)
        )


@pytest.fixture()
async def other_project_fixture(
    db_engine: SAEngine,
    domain_fixture: DomainFixtureData,
    resource_policy_fixture: str,
) -> AsyncIterator[uuid.UUID]:
    """Insert another project for cross-project isolation tests."""
    project_id = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(ProjectRow.__table__).values(
                id=project_id,
                name=f"other-project-{secrets.token_hex(6)}",
                description="Secondary test project",
                is_active=True,
                domain_name=domain_fixture.domain_name,
                resource_policy=resource_policy_fixture,
            )
        )
        virtual_entity_id = uuid.uuid4()
        await conn.execute(
            sa.insert(VirtualEntityRow.__table__).values(
                id=virtual_entity_id,
                entity_type=ScopeType.PROJECT,
                entity_id=project_id,
            )
        )
        await conn.execute(
            sa.insert(EntityMembershipRow.__table__).values(
                virtual_entity_id=virtual_entity_id,
                member_entity_id=virtual_entity_id,
                capped=False,
            )
        )
        await conn.execute(
            sa.insert(ScopeBindingRow.__table__).values(
                virtual_entity_id=virtual_entity_id,
                scope_entity_id=virtual_entity_id,
                permission_cap=None,
            )
        )
    yield project_id
    async with db_engine.begin() as conn:
        await conn.execute(
            VirtualEntityRow.__table__.delete().where(
                VirtualEntityRow.__table__.c.entity_type == ScopeType.PROJECT,
                VirtualEntityRow.__table__.c.entity_id == project_id,
            )
        )
        await conn.execute(
            ProjectRow.__table__.delete().where(ProjectRow.__table__.c.id == project_id)
        )


@pytest.fixture()
async def member_role_fixture(
    db_engine: SAEngine,
    target_project_fixture: uuid.UUID,
) -> AsyncIterator[uuid.UUID]:
    """A project-scoped member role granting USER:READ on the target project.

    Registers the role itself in the project scope (ASE) so revoke_role()
    can detect it as project-scoped, and grants USER:READ permission so the
    holder can pass the scope RBAC validator on user.search_by_project.
    """
    role_id = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(RoleRow.__table__).values(
                id=role_id,
                name=f"test-member-{secrets.token_hex(4)}",
                status=RoleStatus.ACTIVE,
                scope_type=ScopeType.PROJECT.value,
                scope_id=target_project_fixture,
            )
        )
        await conn.execute(
            sa.insert(PermissionRow.__table__).values(
                role_id=role_id,
                entity_type=EntityType.USER,
                permission=Permission.READ,
            )
        )
    yield role_id
    async with db_engine.begin() as conn:
        await conn.execute(
            PermissionRow.__table__.delete().where(PermissionRow.__table__.c.role_id == role_id)
        )
        await conn.execute(RoleRow.__table__.delete().where(RoleRow.__table__.c.id == role_id))


# ---------------------------------------------------------------------------
# V2 SDK client registries
# ---------------------------------------------------------------------------


@pytest.fixture()
async def admin_v2_registry(
    server: ServerInfo,
    admin_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
    """Create a V2ClientRegistry with superadmin keypair for v2 REST endpoints."""
    registry = await V2ClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(
            access_key=admin_user_fixture.keypair.access_key,
            secret_key=admin_user_fixture.keypair.secret_key,
        ),
    )
    try:
        yield registry
    finally:
        await registry.close()


@pytest.fixture()
async def user_v2_registry(
    server: ServerInfo,
    regular_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
    """V2ClientRegistry authenticated as a regular (non-admin) user."""
    registry = await V2ClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(
            access_key=regular_user_fixture.keypair.access_key,
            secret_key=regular_user_fixture.keypair.secret_key,
        ),
    )
    try:
        yield registry
    finally:
        await registry.close()


# ---------------------------------------------------------------------------
# Pre-assigned users fixture (for unassign tests)
# ---------------------------------------------------------------------------


@pytest.fixture()
async def assigned_users(
    db_engine: SAEngine,
    group_fixture: uuid.UUID,
    domain_fixture: DomainFixtureData,
    resource_policy_fixture: str,
    virtual_entity_seeder: VirtualEntitySeeder,
) -> AsyncIterator[list[uuid.UUID]]:
    """Insert test users and enroll them in the target project.

    Yields a list of user UUIDs enrolled in the project's virtual entity.
    Teardown removes the enrollment, keypairs, and users.
    """
    user_ids: list[uuid.UUID] = []
    emails: list[str] = []
    access_keys: list[str] = []

    async with db_engine.begin() as conn:
        for i in range(3):
            uid = uuid.uuid4()
            unique = secrets.token_hex(4)
            email = f"assigned-user-{i}-{unique}@test.local"
            ak = f"AKASSN{secrets.token_hex(7).upper()}"

            await conn.execute(
                sa.insert(users).values(
                    uuid=str(uid),
                    username=f"assigned-user-{i}-{unique}",
                    email=email,
                    password=PasswordInfo(
                        password=secrets.token_urlsafe(8),
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=600_000,
                        salt_size=32,
                    ),
                    need_password_change=False,
                    full_name=f"Assigned User {i}",
                    description=f"Test assigned user {i}",
                    status=UserStatus.ACTIVE,
                    status_info="admin-requested",
                    domain_name=domain_fixture.domain_name,
                    resource_policy=resource_policy_fixture,
                    role=UserRole.USER,
                    domain_id=sa.select(DomainRow.id)
                    .where(DomainRow.name == domain_fixture.domain_name)
                    .scalar_subquery(),
                )
            )
            await conn.execute(
                sa.insert(keypairs).values(
                    access_key=ak,
                    secret_key=SecretValue(secrets.token_hex(20)),
                    is_active=True,
                    is_default=True,
                    resource_policy=resource_policy_fixture,
                    rate_limit=30000,
                    num_queries=0,
                    is_admin=False,
                    user=str(uid),
                )
            )
            await virtual_entity_seeder.insert_user_scope(conn, UserID(uid))
            await virtual_entity_seeder.enroll_user_in_project(conn, group_fixture, UserID(uid))
            user_ids.append(uid)
            emails.append(email)
            access_keys.append(ak)

    yield user_ids

    async with db_engine.begin() as conn:
        for uid in reversed(user_ids):
            await conn.execute(
                VirtualEntityRow.__table__.delete().where(
                    VirtualEntityRow.__table__.c.entity_type == ScopeType.USER,
                    VirtualEntityRow.__table__.c.entity_id == str(uid),
                )
            )
        for ak in reversed(access_keys):
            await conn.execute(keypairs.delete().where(keypairs.c.access_key == ak))
        for uid in reversed(user_ids):
            await conn.execute(users.delete().where(users.c.uuid == str(uid)))
