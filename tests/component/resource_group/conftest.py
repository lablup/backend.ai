"""Component test fixtures for resource group allow/disallow v2 REST API."""

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
from ai.backend.manager.api.adapters.resource_group import ResourceGroupAdapter
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.resource_group.handler import V2ResourceGroupHandler
from ai.backend.manager.api.rest.v2.resource_group.registry import (
    register_v2_resource_group_routes,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.scaling_group.repository import ScalingGroupRepository
from ai.backend.manager.services.processors import Processors
from ai.backend.manager.services.scaling_group.processors import ScalingGroupProcessors
from ai.backend.manager.services.scaling_group.service import ScalingGroupService


@pytest.fixture()
def scaling_group_processors(
    database_engine: ExtendedAsyncSAEngine,
) -> ScalingGroupProcessors:
    repo = ScalingGroupRepository(database_engine)
    service = ScalingGroupService(repo)
    return ScalingGroupProcessors(
        service=service,
        action_monitors=[],
        validators=MagicMock(spec=ActionValidators),
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    scaling_group_processors: ScalingGroupProcessors,
) -> list[RouteRegistry]:
    """Register v2 resource group REST routes for testing."""
    processors = MagicMock(spec=Processors)
    processors.scaling_group = scaling_group_processors

    adapter = ResourceGroupAdapter(processors)
    handler = V2ResourceGroupHandler(adapter=adapter)

    v2_reg = RouteRegistry.create("v2", route_deps.cors_options)
    v2_reg.add_subregistry(register_v2_resource_group_routes(handler, route_deps))
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
