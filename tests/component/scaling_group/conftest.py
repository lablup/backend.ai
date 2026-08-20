from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.resource_group import RESOURCE_GROUP_ENTITY_TYPE
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.scaling_group.handler import ScalingGroupHandler
from ai.backend.manager.api.rest.scaling_group.registry import register_scaling_group_routes
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.scaling_group.repository import ScalingGroupRepository
from ai.backend.manager.services.scaling_group.processors import ScalingGroupProcessors
from ai.backend.manager.services.scaling_group.service import ScalingGroupService


@pytest.fixture()
def scaling_group_processors(
    database_engine: ExtendedAsyncSAEngine, processor_registry: ProcessorRegistry[Any]
) -> ScalingGroupProcessors:
    repo = ScalingGroupRepository(database_engine)
    service = ScalingGroupService(repo)
    return ScalingGroupProcessors(
        processor_registry.group(GroupMeta(RESOURCE_GROUP_ENTITY_TYPE)), service
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    scaling_group_processors: ScalingGroupProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for scaling-group tests."""
    return [
        register_scaling_group_routes(
            ScalingGroupHandler(scaling_group=scaling_group_processors), route_deps
        ),
    ]
