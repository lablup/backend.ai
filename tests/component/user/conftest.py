from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import yarl
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.user import (
    CreateUserRequest,
    CreateUserResponse,
    PurgeUserRequest,
    UserStatus,
)
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.actions.validators.rbac import RBACValidators
from ai.backend.manager.api.adapters.user.adapter import UserAdapter
from ai.backend.manager.api.rest.admin.handler import AdminHandler
from ai.backend.manager.api.rest.admin.registry import register_admin_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.user.handler import UserHandler
from ai.backend.manager.api.rest.user.registry import register_user_routes
from ai.backend.manager.api.rest.v2.user.handler import V2UserHandler
from ai.backend.manager.api.rest.v2.user.registry import register_v2_user_routes
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.group import association_groups_users
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.user import users
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.services.processors import Processors
from ai.backend.manager.services.user.processors import UserProcessors
from ai.backend.manager.services.user.service import UserService
from ai.backend.testutils.fixtures import DomainFixtureData

if TYPE_CHECKING:
    from tests.component.conftest import ServerInfo, UserFixtureData

UserFactory = Callable[..., Coroutine[Any, Any, CreateUserResponse]]


def _create_mock_validators() -> MagicMock:
    mock_rbac = MagicMock(spec=RBACValidators)
    mock_rbac.scope = AsyncMock()
    mock_rbac.single_entity = AsyncMock()
    mock_validators = MagicMock(spec=ActionValidators)
    mock_validators.rbac = mock_rbac
    return mock_validators


@pytest.fixture()
def user_processors(
    database_engine: ExtendedAsyncSAEngine,
    storage_manager: StorageSessionManager,
    agent_registry: AgentRegistry,
    valkey_clients: Any,
) -> UserProcessors:
    user_repository = UserRepository(database_engine)
    service = UserService(
        storage_manager=storage_manager,
        valkey_stat_client=valkey_clients.stat,
        agent_registry=agent_registry,
        user_repository=user_repository,
        scheduling_controller=AsyncMock(),
    )
    return UserProcessors(
        user_service=service, action_monitors=[], validators=_create_mock_validators()
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    user_processors: UserProcessors,
    config_provider: ManagerConfigProvider,
) -> list[RouteRegistry]:
    """Load only the modules required for user-domain tests."""
    user_registry = register_user_routes(
        UserHandler(user=user_processors, config_provider=config_provider),
        route_deps,
    )
    admin_registry = register_admin_routes(
        AdminHandler(
            gql_schema=MagicMock(),
            gql_deps=MagicMock(),
            strawberry_schema=MagicMock(),
            public_strawberry_schema=MagicMock(),
        ),
        route_deps,
        sub_registries=[user_registry],
        gql_ws_handler=MagicMock(),
    )

    # v2 user routes (/v2/users) — exercises the api/adapters/user adapter shared with GQL.
    processors = MagicMock(spec=Processors)
    processors.user = user_processors
    v2_handler = V2UserHandler(adapter=UserAdapter(processors, auth_config=MagicMock()))
    v2_registry = RouteRegistry.create("v2", route_deps.cors_options)
    v2_registry.add_subregistry(register_v2_user_routes(v2_handler, route_deps))

    return [admin_registry, v2_registry]


@pytest.fixture()
async def admin_v2_registry(
    server: ServerInfo,
    admin_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
    """V2ClientRegistry authenticated as superadmin, for /v2/users endpoints."""
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
async def user_factory(
    admin_registry: BackendAIClientRegistry,
    domain_fixture: DomainFixtureData,
    resource_policy_fixture: str,
    db_engine: SAEngine,
) -> AsyncIterator[UserFactory]:
    """Factory fixture that creates users via SDK and purges them on teardown."""
    created_ids: list[uuid.UUID] = []

    async def _create(**overrides: Any) -> CreateUserResponse:
        unique = secrets.token_hex(4)
        params: dict[str, Any] = {
            "email": f"test-{unique}@test.local",
            "username": f"test-{unique}",
            "password": "test-password-1234",
            "domain_name": domain_fixture.domain_name,
            "resource_policy": resource_policy_fixture,
            "status": UserStatus.ACTIVE,
        }
        params.update(overrides)
        result = await admin_registry.user.create(CreateUserRequest(**params))
        created_ids.append(result.user.id)
        return result

    yield _create

    for uid in reversed(created_ids):
        try:
            await admin_registry.user.purge(PurgeUserRequest(user_id=uid))
        except Exception:
            # Fallback: remove user rows directly when the API purge cannot complete.
            # This handles cases where the server is unreachable during teardown.
            async with db_engine.begin() as conn:
                await conn.execute(
                    association_groups_users.delete().where(
                        association_groups_users.c.user_id == str(uid)
                    )
                )
                await conn.execute(keypairs.delete().where(keypairs.c.user == str(uid)))
                await conn.execute(users.delete().where(users.c.uuid == str(uid)))


@pytest.fixture()
async def target_user(
    user_factory: UserFactory,
) -> CreateUserResponse:
    """Pre-created user for tests that need an existing user."""
    return await user_factory()


# --------------------------------------------------------------------------- #
# Data-setup fixtures for v2 container UID/GID filter tests.
# --------------------------------------------------------------------------- #


@dataclass
class ScalarMatchUsers:
    """A user matching a scalar container value (uid / main gid) and one that does not."""

    value: int
    matching: CreateUserResponse
    other: CreateUserResponse


@dataclass
class ArrayMatchUsers:
    """Users for container_gids array filter scenarios."""

    query: list[int]
    matching: CreateUserResponse
    other: CreateUserResponse


@dataclass
class SingleGidUsers:
    """One gid value present as one user's main gid and another user's supplementary gid."""

    gid: int
    via_main_gid: CreateUserResponse
    via_gids: CreateUserResponse
    unrelated: CreateUserResponse


@pytest.fixture()
async def container_uid_users(user_factory: UserFactory) -> ScalarMatchUsers:
    return ScalarMatchUsers(
        value=4001,
        matching=await user_factory(container_uid=4001),
        other=await user_factory(container_uid=4002),
    )


@pytest.fixture()
async def container_main_gid_users(user_factory: UserFactory) -> ScalarMatchUsers:
    return ScalarMatchUsers(
        value=5001,
        matching=await user_factory(container_main_gid=5001),
        other=await user_factory(container_main_gid=5002),
    )


@pytest.fixture()
async def container_gids_any_users(user_factory: UserFactory) -> ArrayMatchUsers:
    return ArrayMatchUsers(
        query=[6020, 6099],
        matching=await user_factory(container_gids=[6010, 6020]),
        other=await user_factory(container_gids=[6030]),
    )


@pytest.fixture()
async def container_gids_all_users(user_factory: UserFactory) -> ArrayMatchUsers:
    return ArrayMatchUsers(
        query=[7010, 7020],
        matching=await user_factory(container_gids=[7010, 7020, 7030]),
        other=await user_factory(container_gids=[7010]),
    )


@pytest.fixture()
async def single_gid_users(user_factory: UserFactory) -> SingleGidUsers:
    gid = 8000
    return SingleGidUsers(
        gid=gid,
        via_main_gid=await user_factory(container_main_gid=gid),
        via_gids=await user_factory(container_gids=[gid, 8001]),
        unrelated=await user_factory(container_main_gid=9000, container_gids=[9001]),
    )
