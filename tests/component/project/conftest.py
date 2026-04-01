"""Component test fixtures for project v2 unassign-users endpoint."""

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

if TYPE_CHECKING:
    from tests.component.conftest import ServerInfo, UserFixtureData

from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.actions.validators.rbac import RBACValidators
from ai.backend.manager.actions.validators.rbac.scope import ScopeActionRBACValidator
from ai.backend.manager.actions.validators.rbac.single_entity import SingleEntityActionRBACValidator
from ai.backend.manager.api.adapters.project import ProjectAdapter
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.project.handler import V2ProjectHandler
from ai.backend.manager.api.rest.v2.project.registry import register_v2_project_routes
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import EntityType, OperationType, ScopeType
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.group import association_groups_users
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.user import users
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.group.repositories import GroupRepositories
from ai.backend.manager.repositories.group.repository import GroupRepository
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.manager.services.group.processors import GroupProcessors
from ai.backend.manager.services.group.service import GroupService
from ai.backend.manager.services.processors import Processors


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
def group_processors(
    database_engine: ExtendedAsyncSAEngine,
    storage_manager: AsyncMock,
    config_provider: MagicMock,
    valkey_clients: MagicMock,
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
    permission_repo = PermissionControllerRepository(database_engine)
    return GroupProcessors(
        group_service=service,
        action_monitors=[],
        validators=ActionValidators(
            rbac=RBACValidators(
                scope=ScopeActionRBACValidator(permission_repo),
                single_entity=SingleEntityActionRBACValidator(permission_repo),
            ),
        ),
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    group_processors: GroupProcessors,
) -> list[RouteRegistry]:
    """Register v2 project REST routes for testing."""
    processors = MagicMock(spec=Processors)
    processors.group = group_processors

    adapter = ProjectAdapter(processors)
    handler = V2ProjectHandler(adapter=adapter)

    v2_reg = RouteRegistry.create("v2", route_deps.cors_options)
    v2_reg.add_subregistry(register_v2_project_routes(handler, route_deps))
    return [v2_reg]


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
async def assigned_users(
    db_engine: SAEngine,
    group_fixture: uuid.UUID,
    domain_fixture: str,
    resource_policy_fixture: str,
) -> AsyncIterator[list[uuid.UUID]]:
    """Insert test users and assign them to the target project.

    Yields a list of user UUIDs that are assigned to *group_fixture*.
    Teardown removes the association, keypairs, and users.
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
                    domain_name=domain_fixture,
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
                sa.insert(association_groups_users).values(
                    group_id=str(group_fixture),
                    user_id=str(uid),
                )
            )
            user_ids.append(uid)
            emails.append(email)
            access_keys.append(ak)

    yield user_ids

    async with db_engine.begin() as conn:
        for uid in reversed(user_ids):
            await conn.execute(
                association_groups_users.delete().where(
                    association_groups_users.c.user_id == str(uid)
                )
            )
        for ak in reversed(access_keys):
            await conn.execute(keypairs.delete().where(keypairs.c.access_key == ak))
        for uid in reversed(user_ids):
            await conn.execute(users.delete().where(users.c.uuid == str(uid)))
