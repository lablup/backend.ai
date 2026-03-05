from __future__ import annotations

import pytest

from ai.backend.manager.api.rest.acl.handler import AclHandler
from ai.backend.manager.api.rest.acl.registry import register_acl_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps


@pytest.fixture()
def server_module_registries(route_deps: RouteDeps) -> list[RouteRegistry]:
    """Load only the modules required for ACL-domain tests."""
    return [
        register_acl_routes(AclHandler(), route_deps),
    ]
