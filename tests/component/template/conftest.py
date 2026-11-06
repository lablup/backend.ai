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
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.actions.validators.rbac import RBACValidators
from ai.backend.manager.api.rest.cluster_template.handler import ClusterTemplateHandler
from ai.backend.manager.api.rest.cluster_template.registry import register_cluster_template_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.session_template.handler import SessionTemplateHandler
from ai.backend.manager.api.rest.session_template.registry import register_session_template_routes
from ai.backend.manager.api.rest.template.registry import register_template_routes
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.dependencies.infrastructure.redis import ValkeyClients
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.session_template import session_templates
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.user import users
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.group.repositories import GroupRepositories
from ai.backend.manager.repositories.group.repository import GroupRepository
from ai.backend.manager.repositories.template.repository import TemplateRepository
from ai.backend.manager.services.group.processors import GroupProcessors
from ai.backend.manager.services.group.service import GroupService
from ai.backend.manager.services.template.processors import TemplateProcessors
from ai.backend.manager.services.template.service import TemplateService
from ai.backend.testutils.fixtures import DomainFixtureData

if TYPE_CHECKING:
    from tests.component.conftest import ServerInfo


def _mock_action_validators() -> MagicMock:
    mock_rbac = MagicMock(spec=RBACValidators)
    mock_rbac.scope = AsyncMock()
    mock_rbac.single_entity = AsyncMock()
    mock_validators = MagicMock(spec=ActionValidators)
    mock_validators.rbac = mock_rbac
    return mock_validators


@pytest.fixture()
def template_processors(database_engine: ExtendedAsyncSAEngine) -> TemplateProcessors:
    repo = TemplateRepository(database_engine)
    service = TemplateService(repository=repo)
    return TemplateProcessors(
        service=service, action_monitors=[], validators=_mock_action_validators()
    )


@pytest.fixture()
def group_processors(
    database_engine: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
    valkey_clients: ValkeyClients,
    storage_manager: StorageSessionManager,
) -> GroupProcessors:
    group_repo = GroupRepository(
        database_engine, config_provider, valkey_clients.stat, storage_manager
    )
    group_repos = GroupRepositories(repository=group_repo)
    service = GroupService(storage_manager, config_provider, valkey_clients.stat, group_repos)
    return GroupProcessors(
        group_service=service, action_monitors=[], validators=_mock_action_validators()
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    template_processors: TemplateProcessors,
    group_processors: GroupProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for template-domain tests."""
    session_tpl_registry = register_session_template_routes(
        SessionTemplateHandler(template=template_processors, group=group_processors),
        route_deps,
    )
    cluster_tpl_registry = register_cluster_template_routes(
        ClusterTemplateHandler(template=template_processors, group=group_processors),
        route_deps,
    )
    return [
        register_template_routes(
            route_deps, sub_registries=[session_tpl_registry, cluster_tpl_registry]
        ),
    ]


@pytest.fixture()
async def group_name_fixture(
    db_engine: SAEngine,
    group_fixture: uuid.UUID,
) -> str:
    """Query the group name from the database for the test group."""
    async with db_engine.begin() as conn:
        result = await conn.execute(
            sa.select(GroupRow.__table__.c.name).where(GroupRow.__table__.c.id == group_fixture)
        )
        row = result.first()
        assert row is not None
        return str(row[0])


@pytest.fixture()
async def outsider_keypair(
    db_engine: SAEngine,
    domain_fixture: DomainFixtureData,
    resource_policy_fixture: str,
) -> AsyncIterator[tuple[str, str]]:
    """A regular user of the same domain who is not in the test project."""
    unique_id = secrets.token_hex(4)
    email = f"outsider-{unique_id}@test.local"
    user_uuid = uuid.uuid4()
    access_key = f"AKTEST{secrets.token_hex(7).upper()}"
    secret_key = secrets.token_hex(20)
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(users).values(
                uuid=str(user_uuid),
                username=f"outsider-{unique_id}",
                email=email,
                password=PasswordInfo(
                    password=secrets.token_urlsafe(8),
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=600_000,
                    salt_size=32,
                ),
                need_password_change=False,
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
                access_key=access_key,
                secret_key=secret_key,
                is_active=True,
                resource_policy=resource_policy_fixture,
                rate_limit=30000,
                num_queries=0,
                is_admin=False,
                user=str(user_uuid),
            )
        )
        await conn.execute(
            users.update().where(users.c.uuid == str(user_uuid)).values(main_access_key=access_key)
        )
    yield access_key, secret_key
    async with db_engine.begin() as conn:
        await conn.execute(
            session_templates.delete().where(session_templates.c.user_uuid == str(user_uuid))
        )
        await conn.execute(
            users.update().where(users.c.uuid == str(user_uuid)).values(main_access_key=None)
        )
        await conn.execute(keypairs.delete().where(keypairs.c.access_key == access_key))
        await conn.execute(users.delete().where(users.c.uuid == str(user_uuid)))


@pytest.fixture()
async def outsider_registry(
    server: ServerInfo,
    outsider_keypair: tuple[str, str],
) -> AsyncIterator[BackendAIClientRegistry]:
    access_key, secret_key = outsider_keypair
    registry = await BackendAIClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(access_key=access_key, secret_key=secret_key),
    )
    try:
        yield registry
    finally:
        await registry.close()
