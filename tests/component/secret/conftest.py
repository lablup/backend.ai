"""Component test fixtures for the stored secret operations."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
import yarl

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.v2_registry import V2ClientRegistry

if TYPE_CHECKING:
    from tests.component.conftest import ServerInfo, UserFixtureData

from ai.backend.common.data.entity.secret import SECRET_ENTITY_TYPE
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta
from ai.backend.manager.api.adapters.secret.adapter import SecretAdapter
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.secret.handler import V2SecretHandler
from ai.backend.manager.api.rest.v2.secret.registry import register_v2_secret_routes
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.secret.provider import SecretOpsProvider
from ai.backend.manager.repositories.secret.repository import SecretRepository
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.services.processors import Processors
from ai.backend.manager.services.secret.processors import SecretProcessors
from ai.backend.manager.services.secret.service import SecretService


@pytest.fixture()
def secret_processors(
    database_engine: ExtendedAsyncSAEngine,
    processor_registry: ProcessorRegistry[Any],
) -> SecretProcessors:
    """Build SecretProcessors with a real DB source."""
    pool = KeyProviderPool(providers=[], write_provider_type=KeyProviderType.PLAIN)
    repository = SecretRepository(SecretOpsProvider(database_engine), pool)
    return SecretProcessors(
        processor_registry.group(GroupMeta(SECRET_ENTITY_TYPE)),
        SecretService(repository),
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    secret_processors: SecretProcessors,
) -> list[RouteRegistry]:
    """Register v2 secret REST routes for testing."""
    processors = MagicMock(spec=Processors)
    processors.secret = secret_processors

    handler = V2SecretHandler(adapter=SecretAdapter(processors))
    v2_reg = RouteRegistry.create("v2", route_deps.cors_options)
    v2_reg.add_subregistry(register_v2_secret_routes(handler, route_deps))
    return [v2_reg]


@pytest.fixture()
async def admin_v2_registry(
    server: ServerInfo,
    admin_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
    """Create a V2ClientRegistry with a superadmin keypair."""
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
    """Create a V2ClientRegistry with a regular user's keypair."""
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
