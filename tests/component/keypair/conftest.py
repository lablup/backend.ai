"""Component test fixtures for admin keypair v2 CRUD."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
import yarl

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.v2_registry import V2ClientRegistry

if TYPE_CHECKING:
    from tests.component.conftest import ServerInfo, UserFixtureData

from ai.backend.manager.api.adapters.user import UserAdapter
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.keypair.handler import V2KeypairHandler
from ai.backend.manager.api.rest.v2.keypair.registry import register_v2_keypair_routes
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.services.processors import Processors
from ai.backend.manager.services.user.processors import UserProcessors
from ai.backend.manager.services.user.service import UserService


@pytest.fixture()
def user_processors(
    database_engine: ExtendedAsyncSAEngine,
) -> UserProcessors:
    """Build UserProcessors with a real DB source for keypair tests."""
    user_repo = UserRepository(database_engine)
    user_service = UserService(
        storage_manager=MagicMock(spec=StorageSessionManager),
        valkey_stat_client=MagicMock(),
        agent_registry=MagicMock(),
        user_repository=user_repo,
    )
    return UserProcessors(
        user_service=user_service,
        action_monitors=[],
        validators=MagicMock(),  # Needs unrestricted mock for nested rbac.scope access
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    user_processors: UserProcessors,
) -> list[RouteRegistry]:
    """Register v2 keypair REST routes for testing."""
    processors = MagicMock(spec=Processors)
    processors.user = user_processors

    adapter = UserAdapter(processors, auth_config=MagicMock())

    handler = V2KeypairHandler(adapter=adapter)
    v2_reg = RouteRegistry.create("v2", route_deps.cors_options)
    v2_reg.add_subregistry(register_v2_keypair_routes(handler, route_deps))
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
