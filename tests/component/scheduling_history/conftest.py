from __future__ import annotations

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
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.scheduling_history.repository import (
    SchedulingHistoryRepository,
)
from ai.backend.manager.services.auth.processors import AuthProcessors
from ai.backend.manager.services.scheduling_history.processors import SchedulingHistoryProcessors
from ai.backend.manager.services.scheduling_history.service import SchedulingHistoryService


@pytest.fixture()
def scheduling_history_processors(
    database_engine: ExtendedAsyncSAEngine,
) -> SchedulingHistoryProcessors:
    repo = SchedulingHistoryRepository(database_engine)
    service = SchedulingHistoryService(repo)
    return SchedulingHistoryProcessors(service=service, action_monitors=[])


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    auth_processors: AuthProcessors,
    scheduling_history_processors: SchedulingHistoryProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for scheduling-history domain tests."""
    return [
        register_auth_routes(AuthHandler(auth=auth_processors), route_deps),
        register_scheduling_history_routes(
            SchedulingHistoryHandler(scheduling_history=scheduling_history_processors),
            route_deps,
        ),
    ]
