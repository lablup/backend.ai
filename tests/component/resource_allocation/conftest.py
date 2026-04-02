"""Component test fixtures for resource allocation v2 REST API."""

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

from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.api.adapters.resource_allocation import ResourceAllocationAdapter
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.resource_allocation.handler import (
    V2ResourceAllocationHandler,
)
from ai.backend.manager.api.rest.v2.resource_allocation.registry import (
    register_v2_resource_allocation_routes,
)
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.dependencies.infrastructure.redis import ValkeyClients
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.resource_allocation.repository import (
    ResourceAllocationRepository,
)
from ai.backend.manager.repositories.resource_preset.repository import (
    ResourcePresetRepository,
)
from ai.backend.manager.services.processors import Processors
from ai.backend.manager.services.resource_allocation.processors import (
    ResourceAllocationProcessors,
)
from ai.backend.manager.services.resource_allocation.service import (
    ResourceAllocationService,
)


@pytest.fixture()
def resource_allocation_processors(
    database_engine: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
    valkey_clients: ValkeyClients,
) -> ResourceAllocationProcessors:
    """Build real resource allocation processors with real DB and config."""
    ra_repo = ResourceAllocationRepository(
        db=database_engine,
        config_provider=config_provider,
    )
    rp_repo = ResourcePresetRepository(
        db=database_engine,
        valkey_stat=valkey_clients.stat,
        config_provider=config_provider,
    )
    service = ResourceAllocationService(
        resource_allocation_repository=ra_repo,
        resource_preset_repository=rp_repo,
    )
    return ResourceAllocationProcessors(
        service=service,
        action_monitors=[],
        validators=MagicMock(spec=ActionValidators),
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    resource_allocation_processors: ResourceAllocationProcessors,
    config_provider: ManagerConfigProvider,
) -> list[RouteRegistry]:
    """Register v2 resource allocation REST routes for testing."""
    processors = MagicMock(spec=Processors)
    processors.resource_allocation = resource_allocation_processors

    adapter = ResourceAllocationAdapter(
        processors=processors,
        config_provider=config_provider,
    )
    handler = V2ResourceAllocationHandler(adapter=adapter)

    v2_reg = RouteRegistry.create("v2", route_deps.cors_options)
    v2_reg.add_subregistry(register_v2_resource_allocation_routes(handler, route_deps))
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
async def user_v2_registry(
    server: ServerInfo,
    regular_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
    """Create a V2ClientRegistry with regular user keypair for v2 REST endpoints."""
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
