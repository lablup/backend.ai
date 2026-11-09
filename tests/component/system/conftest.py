from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

import pytest
import yarl

from ai.backend.client.v2.auth import NoAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps

if TYPE_CHECKING:
    from tests.component.conftest import ServerInfo


@pytest.fixture()
def server_module_registries(route_deps: RouteDeps) -> list[RouteRegistry]:
    """No modules needed — the hello() handler is on the root app."""
    return []


@pytest.fixture()
async def anonymous_registry(server: ServerInfo) -> AsyncIterator[BackendAIClientRegistry]:
    registry = await BackendAIClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)), NoAuth()
    )
    try:
        yield registry
    finally:
        await registry.close()
