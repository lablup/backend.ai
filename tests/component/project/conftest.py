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
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
import yarl
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.data.permission.types import RelationType
from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.actions.validators.rbac import RBACValidators
from ai.backend.manager.actions.validators.rbac.bulk import BulkActionRBACValidator
from ai.backend.manager.actions.validators.rbac.scope import ScopeActionRBACValidator
from ai.backend.manager.actions.validators.rbac.single_entity import SingleEntityActionRBACValidator
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
    OperationType,
    Permission,
    ScopeType,
)
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.dependencies.infrastructure.redis import ValkeyClients
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.user import users
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.group.repositories import GroupRepositories
from ai.backend.manager.repositories.group.repository import GroupRepository
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.services.group.processors import GroupProcessors
from ai.backend.manager.services.group.service import GroupService
from ai.backend.manager.services.permission_contoller.processors import (
    PermissionControllerProcessors,
)
from ai.backend.manager.services.permission_contoller.service import PermissionControllerService
from ai.backend.manager.services.processors import Processors
from ai.backend.manager.services.user.processors import UserProcessors
from ai.backend.manager.services.user.service import UserService
from ai.backend.testutils.fixtures import DomainFixtureData

if TYPE_CHECKING:
    from tests.component.conftest import ServerInfo, UserFixtureData


def _build_validators(
    database_engine: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
) -> ActionValidators:
    permission_repo = PermissionControllerRepository(database_engine)
    return ActionValidators(
        rbac=RBACValidators(
            scope=ScopeActionRBACValidator(permission_repo, config_provider, MagicMock()),
            single_entity=SingleEntityActionRBACValidator(
                permission_repo, config_provider, MagicMock()
            ),
            bulk=BulkActionRBACValidator(permission_repo, config_provider),
        ),
    )


# ---------------------------------------------------------------------------
# Processor fixtures (real DB, real RBAC enforcement)
# ---------------------------------------------------------------------------


@pytest.fixture()
def group_processors(
    database_engine: ExtendedAsyncSAEngine,
    storage_manager: AsyncMock,
    config_provider: ManagerConfigProvider,
    valkey_clients: ValkeyClients,
) -> GroupProcessors:
    """Real DB-backed GroupProcessors with real RBAC validators."""
    repo = GroupRepository(
        database_engine,
        config_provider,
        valkey_clients.stat,
        storage_manager,
    )
    repositories = GroupRepositories(repository=repo)
    service = GroupService(
        storage_manager=storage_manager,
        config_provider=config_provider,
        valkey_stat_client=valkey_clients.stat,
        group_repositories=repositories,
    )
    return GroupProcessors(
        group_service=service,
        action_monitors=[],
        validators=_build_validators(database_engine, config_provider),
    )


@pytest.fixture()
def user_processors(
    database_engine: ExtendedAsyncSAEngine,
    agent_registry: AgentRegistry,
    valkey_clients: ValkeyClients,
    config_provider: ManagerConfigProvider,
) -> UserProcessors:
    """Real UserProcessors for user.search_by_project SDK calls."""
    repo = UserRepository(database_engine)
    service = UserService(
        storage_manager=AsyncMock(),
        valkey_stat_client=valkey_clients.stat,
        agent_registry=agent_registry,
        user_repository=repo,
        scheduling_controller=AsyncMock(),
    )
    return UserProcessors(
        user_service=service,
        action_monitors=[],
        validators=_build_validators(database_engine, config_provider),
    )


@pytest.fixture()
def permission_controller_processors(
    database_engine: ExtendedAsyncSAEngine,
    valkey_clients: ValkeyClients,
    config_provider: ManagerConfigProvider,
) -> PermissionControllerProcessors:
    """Real PermissionControllerProcessors for rbac.assign_role / revoke_role SDK calls."""
    perm_repo = PermissionControllerRepository(database_engine)
    storage_mock = AsyncMock()
    group_repo = GroupRepository(
        database_engine, config_provider, valkey_clients.stat, storage_mock
    )
    service = PermissionControllerService(
        perm_repo, group_repository=group_repo, rbac_action_registry=[]
    )
    return PermissionControllerProcessors(
        service=service,
        action_monitors=[],
        validators=_build_validators(database_engine, config_provider),
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    config_provider: ManagerConfigProvider,
    group_processors: GroupProcessors,
    user_processors: UserProcessors,
    permission_controller_processors: PermissionControllerProcessors,
) -> list[RouteRegistry]:
    """Register v2 project, user, and RBAC routes for testing."""
    processors = MagicMock(spec=Processors)
    processors.group = group_processors
    processors.user = user_processors
    processors.permission_controller = permission_controller_processors

    proj_handler = V2ProjectHandler(adapter=ProjectAdapter(processors))
    user_handler = V2UserHandler(adapter=UserAdapter(processors, config_provider.config.auth))
    rbac_handler = V2RBACHandler(adapter=RBACAdapter(processors))

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
                scope_type=ScopeType.PROJECT,
                scope_id=str(group_fixture),
                entity_type=EntityType.PROJECT,
                operation=OperationType.UPDATE,
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
    against the target project pass ScopeActionRBACValidator.
    """
    role_id = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(RoleRow.__table__).values(
                id=role_id,
                name=f"test-target-admin-{secrets.token_hex(4)}",
                status=RoleStatus.ACTIVE,
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
                scope_type=ScopeType.PROJECT,
                scope_id=str(target_project_fixture),
                entity_type=EntityType.PROJECT,
                operation=OperationType.UPDATE,
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
            sa.insert(GroupRow.__table__).values(
                id=project_id,
                name=f"target-project-{secrets.token_hex(6)}",
                description="Primary test project for membership scenarios",
                is_active=True,
                domain_name=domain_fixture.domain_name,
                resource_policy=resource_policy_fixture,
            )
        )
    yield project_id
    async with db_engine.begin() as conn:
        await conn.execute(GroupRow.__table__.delete().where(GroupRow.__table__.c.id == project_id))


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
            sa.insert(GroupRow.__table__).values(
                id=project_id,
                name=f"other-project-{secrets.token_hex(6)}",
                description="Secondary test project",
                is_active=True,
                domain_name=domain_fixture.domain_name,
                resource_policy=resource_policy_fixture,
            )
        )
    yield project_id
    async with db_engine.begin() as conn:
        await conn.execute(GroupRow.__table__.delete().where(GroupRow.__table__.c.id == project_id))


@pytest.fixture()
async def member_role_fixture(
    db_engine: SAEngine,
    target_project_fixture: uuid.UUID,
) -> AsyncIterator[uuid.UUID]:
    """A project-scoped member role granting USER:READ on the target project.

    Registers the role itself in the project scope (ASE) so revoke_role()
    can detect it as project-scoped, and grants USER:READ permission so the
    holder can pass ScopeActionRBACValidator on user.search_by_project.
    """
    role_id = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(RoleRow.__table__).values(
                id=role_id,
                name=f"test-member-{secrets.token_hex(4)}",
                status=RoleStatus.ACTIVE,
            )
        )
        await conn.execute(
            sa.insert(AssociationScopesEntitiesRow.__table__).values(
                scope_type=ScopeType.PROJECT,
                scope_id=str(target_project_fixture),
                entity_type=EntityType.ROLE,
                entity_id=str(role_id),
                relation_type=RelationType.AUTO,
            )
        )
        await conn.execute(
            sa.insert(PermissionRow.__table__).values(
                role_id=role_id,
                scope_type=ScopeType.PROJECT,
                scope_id=str(target_project_fixture),
                entity_type=EntityType.USER,
                operation=OperationType.READ,
                permission=Permission.READ,
            )
        )
    yield role_id
    async with db_engine.begin() as conn:
        await conn.execute(
            PermissionRow.__table__.delete().where(PermissionRow.__table__.c.role_id == role_id)
        )
        await conn.execute(
            AssociationScopesEntitiesRow.__table__.delete().where(
                sa.and_(
                    AssociationScopesEntitiesRow.__table__.c.entity_type == EntityType.ROLE,
                    AssociationScopesEntitiesRow.__table__.c.entity_id == str(role_id),
                )
            )
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
) -> AsyncIterator[list[uuid.UUID]]:
    """Insert test users and assign them to the target project via ASE.

    Yields a list of user UUIDs whose project membership row is recorded in
    `association_scopes_entities` (PROJECT scope, USER entity).
    Teardown removes the membership row, keypairs, and users.
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
                )
            )
            await conn.execute(
                sa.insert(keypairs).values(
                    user_id=email,
                    access_key=ak,
                    secret_key=secrets.token_hex(20),
                    is_active=True,
                    resource_policy=resource_policy_fixture,
                    rate_limit=30000,
                    num_queries=0,
                    is_admin=False,
                    user=str(uid),
                )
            )
            await conn.execute(
                sa.insert(AssociationScopesEntitiesRow).values(
                    scope_type=ScopeType.PROJECT,
                    scope_id=str(group_fixture),
                    entity_type=EntityType.USER,
                    entity_id=str(uid),
                    relation_type=RelationType.AUTO,
                )
            )
            user_ids.append(uid)
            emails.append(email)
            access_keys.append(ak)

    yield user_ids

    async with db_engine.begin() as conn:
        for uid in reversed(user_ids):
            await conn.execute(
                sa.delete(AssociationScopesEntitiesRow).where(
                    AssociationScopesEntitiesRow.scope_type == ScopeType.PROJECT,
                    AssociationScopesEntitiesRow.scope_id == str(group_fixture),
                    AssociationScopesEntitiesRow.entity_type == EntityType.USER,
                    AssociationScopesEntitiesRow.entity_id == str(uid),
                )
            )
        for ak in reversed(access_keys):
            await conn.execute(keypairs.delete().where(keypairs.c.access_key == ak))
        for uid in reversed(user_ids):
            await conn.execute(users.delete().where(users.c.uuid == str(uid)))
