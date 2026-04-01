"""Component test fixtures for runtime variant v2 CRUD."""

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

from ai.backend.manager.api.adapters.runtime_variant import RuntimeVariantAdapter
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.runtime_variant.handler import V2RuntimeVariantHandler
from ai.backend.manager.api.rest.v2.runtime_variant.registry import (
    register_v2_runtime_variant_routes,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.runtime_variant.repository import RuntimeVariantRepository
from ai.backend.manager.services.processors import Processors
from ai.backend.manager.services.runtime_variant.processors import RuntimeVariantProcessors
from ai.backend.manager.services.runtime_variant.service import RuntimeVariantService


@pytest.fixture()
def runtime_variant_processors(
    database_engine: ExtendedAsyncSAEngine,
) -> RuntimeVariantProcessors:
    repo = RuntimeVariantRepository(database_engine)
    service = RuntimeVariantService(repo)
    return RuntimeVariantProcessors(
        service=service,
        action_monitors=[],
        validators=MagicMock(),
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    runtime_variant_processors: RuntimeVariantProcessors,
) -> list[RouteRegistry]:
    """Register v2 runtime variant REST routes for testing."""
    processors = MagicMock(spec=Processors)
    processors.runtime_variant = runtime_variant_processors

    adapter = RuntimeVariantAdapter(processors)

    handler = V2RuntimeVariantHandler(adapter=adapter)
    v2_reg = RouteRegistry.create("v2", route_deps.cors_options)
    v2_reg.add_subregistry(register_v2_runtime_variant_routes(handler, route_deps))
    return [v2_reg]


@pytest.fixture()
async def admin_v2_registry(
    server: ServerInfo,
    admin_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
    """Create a V2ClientRegistry with superadmin keypair."""
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
