from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ai.backend.manager.api.rest.auth.handler import AuthHandler
from ai.backend.manager.api.rest.auth.registry import register_auth_routes
from ai.backend.manager.api.rest.routing import RouteRegistry

# Statically imported so that Pants includes these modules in the test PEX.
# build_root_app() loads them at runtime via importlib.import_module(),
# which Pants cannot trace statically.
from ai.backend.manager.api.rest.scheduling_history.handler import SchedulingHistoryHandler
from ai.backend.manager.api.rest.scheduling_history.registry import (
    register_scheduling_history_routes,
)
from ai.backend.manager.api.rest.types import RouteDeps


@pytest.fixture()
def server_module_registries(route_deps: RouteDeps) -> list[RouteRegistry]:
    """Load only the modules required for scheduling-history domain tests."""
    mock_processors = MagicMock()
    return [
        register_auth_routes(AuthHandler(auth=mock_processors.auth), route_deps),
        register_scheduling_history_routes(
            SchedulingHistoryHandler(scheduling_history=mock_processors.scheduling_history),
            route_deps,
        ),
    ]
