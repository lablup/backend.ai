from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ai.backend.manager.api.rest.auth.handler import AuthHandler
from ai.backend.manager.api.rest.auth.registry import register_auth_routes
from ai.backend.manager.api.rest.error_log.handler import ErrorLogHandler
from ai.backend.manager.api.rest.error_log.registry import register_error_log_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps


@pytest.fixture()
def server_module_registries(route_deps: RouteDeps) -> list[RouteRegistry]:
    """Load only the modules required for error-log domain tests."""
    mock_processors = MagicMock()
    return [
        register_auth_routes(AuthHandler(auth=mock_processors.auth), route_deps),
        register_error_log_routes(ErrorLogHandler(error_log=mock_processors.error_log), route_deps),
    ]
