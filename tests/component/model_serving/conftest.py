from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ai.backend.manager.api.rest.auth.handler import AuthHandler
from ai.backend.manager.api.rest.auth.registry import register_auth_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.service.handler import ServiceHandler
from ai.backend.manager.api.rest.service.registry import register_service_routes
from ai.backend.manager.api.rest.types import RouteDeps


@pytest.fixture()
def server_module_registries(route_deps: RouteDeps) -> list[RouteRegistry]:
    """Load only the modules required for model-serving tests."""
    mock_processors = MagicMock()
    return [
        register_auth_routes(AuthHandler(processors=mock_processors), route_deps),
        register_service_routes(ServiceHandler(processors=mock_processors), route_deps),
    ]
