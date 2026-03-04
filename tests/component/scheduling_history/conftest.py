from __future__ import annotations

import pytest

from ai.backend.manager.api.rest.auth.registry import register_auth_routes

# Statically imported so that Pants includes these modules in the test PEX.
# build_root_app() loads them at runtime via importlib.import_module(),
# which Pants cannot trace statically.
from ai.backend.manager.api.rest.scheduling_history.registry import (
    register_scheduling_history_routes,
)
from ai.backend.manager.api.rest.types import ModuleRegistrar


@pytest.fixture()
def server_module_registrars() -> list[ModuleRegistrar]:
    """Load only the modules required for scheduling-history domain tests."""
    return [register_auth_routes, register_scheduling_history_routes]
