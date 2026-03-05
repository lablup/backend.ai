from __future__ import annotations

import pytest

from ai.backend.manager.api.rest.auth.handler import AuthHandler
from ai.backend.manager.api.rest.auth.registry import register_auth_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.scaling_group.handler import ScalingGroupHandler
from ai.backend.manager.api.rest.scaling_group.registry import register_scaling_group_routes
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.scaling_group.repository import ScalingGroupRepository
from ai.backend.manager.services.auth.processors import AuthProcessors
from ai.backend.manager.services.scaling_group.processors import ScalingGroupProcessors
from ai.backend.manager.services.scaling_group.service import ScalingGroupService


@pytest.fixture()
def scaling_group_processors(database_engine: ExtendedAsyncSAEngine) -> ScalingGroupProcessors:
    repo = ScalingGroupRepository(database_engine)
    service = ScalingGroupService(repo)
    return ScalingGroupProcessors(service=service, action_monitors=[])


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    auth_processors: AuthProcessors,
    scaling_group_processors: ScalingGroupProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for scaling-group-domain tests."""
    return [
        register_auth_routes(AuthHandler(auth=auth_processors), route_deps),
        register_scaling_group_routes(
            ScalingGroupHandler(scaling_group=scaling_group_processors), route_deps
        ),
    ]
